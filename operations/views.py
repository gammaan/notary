from decimal import Decimal
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView, View

from accounts.forms import UserProfileForm
from accounts.permissions import can_delete_records
from operations.audit import log_audit, log_status_change
from operations.finance import global_finance_summary, matter_finance_summary
from operations.notifications import notify_client_matter_update
from operations.pdf import render_pdf_response
from operations.forms import (
    ClientForm,
    DocumentForm,
    MatterForm,
    MatterWizardClientForm,
    MatterWizardDetailsForm,
    StaffLoginForm,
    TransactionForm,
)
from operations.mixins import ManagerRequiredMixin, StaffRequiredMixin
from operations.models import AppointmentRequest, AuditLog, Client, Document, Matter, ServiceType, Transaction
from operations.filters import filter_clients, filter_documents, filter_matters, filter_transactions
from operations.quick_actions import next_document_status
from operations.transaction_rules import (
    REOPEN_STATUSES,
    apply_matter_status,
    auto_complete_matter_if_paid,
    can_manually_complete_matter,
    matter_is_closed,
    transaction_is_locked,
)
from operations.utils import redirect_if_matter_closed, safe_redirect
from operations.workflow import (
    clear_wizard_data,
    get_wizard_data,
    matter_workflow_steps,
    set_wizard_data,
)


class StaffLoginView(LoginView):
    form_class = StaffLoginForm
    template_name = "operations/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("staff:dashboard")

    def form_valid(self, form):
        messages.success(self.request, f"Welcome, {form.get_user().first_name}.")
        return super().form_valid(form)


class StaffLogoutView(LogoutView):
    next_page = reverse_lazy("staff:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been signed out.")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "operations/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        open_statuses = [
            Matter.Status.INQUIRY,
            Matter.Status.SCHEDULED,
            Matter.Status.IN_PROGRESS,
            Matter.Status.AWAITING_PAYMENT,
        ]
        income_month = (
            Transaction.objects.filter(
                transaction_type=Transaction.Type.INCOME,
                status=Transaction.Status.PAID,
                transaction_date__year=today.year,
                transaction_date__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        ctx["stats"] = {
            "clients": Client.objects.filter(is_active=True).count(),
            "open_matters": Matter.objects.filter(status__in=open_statuses).count(),
            "scheduled_today": Matter.objects.filter(
                scheduled_at__date=today,
                status__in=open_statuses,
            ).count(),
            "pending_payments": Transaction.objects.filter(
                status=Transaction.Status.PENDING,
                transaction_type=Transaction.Type.INCOME,
            ).count(),
            "income_month": income_month,
            "completed_month": Matter.objects.filter(
                status=Matter.Status.COMPLETED,
                completed_at__year=today.year,
                completed_at__month=today.month,
            ).count(),
            "documents_pending": Document.objects.filter(
                status=Document.Status.PENDING,
            ).count(),
            "new_clients_month": Client.objects.filter(
                created_at__year=today.year,
                created_at__month=today.month,
            ).count(),
        }
        ctx["recent_matters"] = (
            Matter.objects.select_related("client", "service_type")
            .order_by("-created_at")[:8]
        )
        ctx["today_matters"] = (
            Matter.objects.filter(scheduled_at__date=today)
            .select_related("client", "service_type")
            .order_by("scheduled_at")
        )
        ctx["pending_transactions"] = (
            Transaction.objects.filter(
                status=Transaction.Status.PENDING,
                transaction_type=Transaction.Type.INCOME,
            )
            .select_related("matter", "matter__client")
            .order_by("transaction_date")[:6]
        )

        status_labels = dict(Matter.Status.choices)
        status_rows = (
            Matter.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        ctx["chart_matter_status"] = {
            "labels": [status_labels.get(row["status"], row["status"]) for row in status_rows],
            "values": [row["count"] for row in status_rows],
        }

        month_labels = []
        month_values = []
        year, month = today.year, today.month
        for offset in range(5, -1, -1):
            m = month - offset
            y = year
            while m <= 0:
                m += 12
                y -= 1
            total = (
                Transaction.objects.filter(
                    transaction_type=Transaction.Type.INCOME,
                    status=Transaction.Status.PAID,
                    transaction_date__year=y,
                    transaction_date__month=m,
                ).aggregate(s=Sum("amount"))["s"]
                or Decimal("0")
            )
            month_labels.append(date(y, m, 1).strftime("%b"))
            month_values.append(float(total))
        ctx["chart_revenue"] = {"labels": month_labels, "values": month_values}

        service_rows = (
            ServiceType.objects.annotate(count=Count("matters"))
            .filter(count__gt=0)
            .order_by("-count")[:6]
        )
        ctx["chart_services"] = {
            "labels": [row.name for row in service_rows],
            "values": [row.count for row in service_rows],
        }
        return ctx


class ClientListView(StaffRequiredMixin, ListView):
    model = Client
    template_name = "operations/clients/list.html"
    context_object_name = "clients"
    paginate_by = 20

    def get_queryset(self):
        qs = Client.objects.annotate(matter_count=Count("matters")).order_by("last_name", "first_name")
        return filter_clients(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filters"] = self.request.GET
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_query"] = params.urlencode()
        ctx["clear_url"] = reverse("staff:client_list")
        return ctx


class ClientCreateView(StaffRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "operations/clients/form.html"

    def get_success_url(self):
        return reverse("staff:client_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Client created successfully.")
        return super().form_valid(form)


class ClientUpdateView(StaffRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "operations/clients/form.html"

    def get_success_url(self):
        return reverse("staff:client_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Client updated successfully.")
        return super().form_valid(form)


class ClientDetailView(StaffRequiredMixin, DetailView):
    model = Client
    template_name = "operations/clients/detail.html"
    context_object_name = "client"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["matters"] = self.object.matters.select_related("service_type").order_by("-created_at")
        return ctx


class MatterListView(StaffRequiredMixin, ListView):
    model = Matter
    template_name = "operations/matters/list.html"
    context_object_name = "matters"
    paginate_by = 20

    def get_queryset(self):
        qs = Matter.objects.select_related("client", "service_type", "assigned_to").order_by("-created_at")
        return filter_matters(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Matter.Status.choices
        ctx["service_types"] = ServiceType.objects.filter(is_active=True).order_by("name")
        ctx["active_status"] = self.request.GET.get("status", "")
        ctx["filters"] = self.request.GET
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_query"] = params.urlencode()
        return ctx


class MatterDetailView(StaffRequiredMixin, DetailView):
    model = Matter
    template_name = "operations/matters/detail.html"
    context_object_name = "matter"

    def get_queryset(self):
        return Matter.objects.select_related("client", "service_type", "assigned_to")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, current = matter_workflow_steps(self.object)
        ctx["workflow_steps"] = steps
        ctx["current_step"] = current
        ctx["documents"] = self.object.documents.order_by("-created_at")
        ctx["transactions"] = self.object.transactions.order_by("-transaction_date")
        ctx["matter_status_choices"] = Matter.Status.choices
        ctx["document_status_choices"] = Document.Status.choices
        ctx["transaction_status_choices"] = Transaction.Status.choices
        ctx["total_billed"] = (
            self.object.transactions.filter(transaction_type=Transaction.Type.INCOME).aggregate(
                s=Sum("amount")
            )["s"]
            or Decimal("0")
        )
        ctx["total_paid"] = (
            self.object.transactions.filter(
                transaction_type=Transaction.Type.INCOME,
                status=Transaction.Status.PAID,
            ).aggregate(s=Sum("amount"))["s"]
            or Decimal("0")
        )
        ctx["matter_is_closed"] = matter_is_closed(self.object)
        documents = list(self.object.documents.order_by("-created_at"))
        status_labels = dict(Document.Status.choices)
        for doc in documents:
            nxt = next_document_status(doc.status)
            doc.approve_target = nxt
            doc.approve_target_label = status_labels.get(nxt, "") if nxt else ""
        ctx["documents"] = documents
        return ctx


class MatterStatusView(StaffRequiredMixin, View):
    def post(self, request, pk):
        matter = get_object_or_404(Matter, pk=pk)
        status = request.POST.get("status")
        if status not in Matter.Status.values:
            messages.error(request, "Invalid status.")
            return redirect("staff:matter_detail", pk=matter.pk)

        old_status = matter.status
        if matter_is_closed(matter):
            if status in REOPEN_STATUSES:
                apply_matter_status(matter, status)
                log_status_change(
                    request.user,
                    AuditLog.EntityType.MATTER,
                    matter,
                    old_status,
                    status,
                    label=matter.reference_number,
                )
                messages.success(request, f"Matter reopened as {matter.get_status_display()}.")
            else:
                messages.error(request, "This matter is closed. Choose an open status to reopen it.")
        elif status == Matter.Status.COMPLETED and not can_manually_complete_matter(matter):
            messages.error(
                request,
                "Cannot mark complete until all income fees are paid or waived.",
            )
        else:
            apply_matter_status(matter, status)
            if old_status != status:
                log_status_change(
                    request.user,
                    AuditLog.EntityType.MATTER,
                    matter,
                    old_status,
                    status,
                    label=matter.reference_number,
                )
                notify_client_matter_update(
                    matter,
                    _("Your matter status is now: %(status)s")
                    % {"status": matter.get_status_display()},
                )
            messages.success(request, f"Matter status updated to {matter.get_status_display()}.")
        return redirect("staff:matter_detail", pk=matter.pk)


class DocumentDownloadView(StaffRequiredMixin, View):
    def get(self, request, pk):
        document = get_object_or_404(Document.objects.select_related("matter"), pk=pk)
        if not document.file:
            messages.error(request, "No file attached to this document.")
            return redirect("staff:matter_detail", pk=document.matter_id)
        try:
            filename = document.file.name.rsplit("/", 1)[-1]
            return FileResponse(
                document.file.open("rb"),
                as_attachment=True,
                filename=filename,
            )
        except FileNotFoundError:
            messages.error(request, "File not found on disk.")
            return redirect("staff:matter_detail", pk=document.matter_id)


class DocumentQuickActionView(StaffRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(Document.objects.select_related("matter"), pk=pk)
        matter = document.matter
        matter_pk = matter.pk
        next_url = request.POST.get("next")
        default = reverse("staff:matter_detail", kwargs={"pk": matter_pk})

        blocked = redirect_if_matter_closed(request, matter)
        if blocked:
            return blocked

        action = request.POST.get("action")

        if action == "delete":
            if not can_delete_records(request.user):
                messages.error(request, "Only managers can delete records.")
                return safe_redirect(request, next_url, "staff:matter_detail", pk=matter_pk)
            title = document.title
            doc_id = document.pk
            document.delete()
            log_audit(
                request.user,
                AuditLog.Action.DELETED,
                AuditLog.EntityType.DOCUMENT,
                doc_id,
                title,
                matter=matter,
            )
            messages.success(request, f'Document "{title}" removed.')
        elif action == "approve":
            nxt = next_document_status(document.status)
            if nxt:
                old_status = document.status
                document.status = nxt
                document.save(update_fields=["status", "updated_at"])
                log_status_change(
                    request.user,
                    AuditLog.EntityType.DOCUMENT,
                    document,
                    old_status,
                    nxt,
                    matter=matter,
                    label=document.title,
                )
                messages.success(request, f'Document marked as {document.get_status_display()}.')
            else:
                messages.info(request, "Document is already at the final review stage.")
        elif action == "status":
            status = request.POST.get("status")
            if status in Document.Status.values:
                old_status = document.status
                document.status = status
                document.save(update_fields=["status", "updated_at"])
                if old_status != status:
                    log_status_change(
                        request.user,
                        AuditLog.EntityType.DOCUMENT,
                        document,
                        old_status,
                        status,
                        matter=matter,
                        label=document.title,
                    )
                messages.success(request, f'Document status set to {document.get_status_display()}.')
            else:
                messages.error(request, "Invalid document status.")
        else:
            messages.error(request, "Unknown action.")

        return safe_redirect(request, next_url, "staff:matter_detail", pk=matter_pk)


class TransactionQuickActionView(StaffRequiredMixin, View):
    def post(self, request, pk):
        transaction = get_object_or_404(
            Transaction.objects.select_related("matter"), pk=pk
        )
        matter = transaction.matter
        matter_pk = matter.pk
        next_url = request.POST.get("next")

        blocked = redirect_if_matter_closed(request, matter)
        if blocked:
            return blocked

        action = request.POST.get("action")

        if transaction_is_locked(transaction) and action in {
            "delete",
            "mark_paid",
            "mark_pending",
            "mark_waived",
            "status",
        }:
            messages.error(
                request,
                "This transaction is locked because it is paid, waived, or cancelled.",
            )
            return safe_redirect(request, next_url, "staff:matter_detail", pk=matter_pk)

        if action == "delete":
            if not can_delete_records(request.user):
                messages.error(request, "Only managers can delete records.")
                return safe_redirect(request, next_url, "staff:matter_detail", pk=matter_pk)
            label = transaction.description
            txn_id = transaction.pk
            transaction.delete()
            log_audit(
                request.user,
                AuditLog.Action.DELETED,
                AuditLog.EntityType.TRANSACTION,
                txn_id,
                label,
                matter=matter,
            )
            messages.success(request, f'Transaction "{label}" removed.')
        elif action == "mark_paid":
            old_status = transaction.status
            transaction.status = Transaction.Status.PAID
            transaction.save(update_fields=["status", "updated_at"])
            log_status_change(
                request.user,
                AuditLog.EntityType.TRANSACTION,
                transaction,
                old_status,
                transaction.status,
                matter=matter,
                label=transaction.description,
            )
            if auto_complete_matter_if_paid(matter):
                messages.success(
                    request,
                    "Payment marked as paid. Matter automatically marked as completed.",
                )
            else:
                messages.success(request, "Payment marked as paid.")
        elif action == "mark_pending":
            old_status = transaction.status
            transaction.status = Transaction.Status.PENDING
            transaction.save(update_fields=["status", "updated_at"])
            log_status_change(
                request.user,
                AuditLog.EntityType.TRANSACTION,
                transaction,
                old_status,
                transaction.status,
                matter=matter,
                label=transaction.description,
            )
            messages.info(request, "Payment marked as pending.")
        elif action == "mark_waived":
            old_status = transaction.status
            transaction.status = Transaction.Status.WAIVED
            transaction.save(update_fields=["status", "updated_at"])
            log_status_change(
                request.user,
                AuditLog.EntityType.TRANSACTION,
                transaction,
                old_status,
                transaction.status,
                matter=matter,
                label=transaction.description,
            )
            if auto_complete_matter_if_paid(matter):
                messages.info(
                    request,
                    "Fee waived. Matter automatically marked as completed.",
                )
            else:
                messages.info(request, "Fee waived.")
        elif action == "status":
            status = request.POST.get("status")
            if status in Transaction.Status.values:
                old_status = transaction.status
                transaction.status = status
                transaction.save(update_fields=["status", "updated_at"])
                if old_status != status:
                    log_status_change(
                        request.user,
                        AuditLog.EntityType.TRANSACTION,
                        transaction,
                        old_status,
                        status,
                        matter=matter,
                        label=transaction.description,
                    )
                if status in {
                    Transaction.Status.PAID,
                    Transaction.Status.WAIVED,
                } and auto_complete_matter_if_paid(matter):
                    messages.success(
                        request,
                        f"Payment status set to {transaction.get_status_display()}. "
                        "Matter automatically marked as completed.",
                    )
                else:
                    messages.success(
                        request,
                        f"Payment status set to {transaction.get_status_display()}.",
                    )
            else:
                messages.error(request, "Invalid payment status.")
        else:
            messages.error(request, "Unknown action.")

        return safe_redirect(request, next_url, "staff:matter_detail", pk=matter_pk)


class DocumentUpdateView(StaffRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "operations/documents/form.html"
    context_object_name = "document"

    def get_queryset(self):
        return Document.objects.select_related("matter")

    def dispatch(self, request, *args, **kwargs):
        if request.method in ("GET", "POST"):
            document = get_object_or_404(
                Document.objects.select_related("matter"), pk=kwargs["pk"]
            )
            blocked = redirect_if_matter_closed(request, document.matter)
            if blocked:
                return blocked
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["matter"] = self.object.matter
        return ctx

    def get_success_url(self):
        return reverse("staff:matter_detail", kwargs={"pk": self.object.matter_id})

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit(
            self.request.user,
            AuditLog.Action.UPDATED,
            AuditLog.EntityType.DOCUMENT,
            self.object.pk,
            self.object.title,
            matter=self.object.matter,
        )
        messages.success(self.request, "Document updated successfully.")
        return response


class TransactionUpdateView(StaffRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "operations/transactions/form.html"
    context_object_name = "transaction"

    def get_queryset(self):
        return Transaction.objects.select_related("matter")

    def dispatch(self, request, *args, **kwargs):
        if request.method in ("GET", "POST"):
            transaction = get_object_or_404(
                Transaction.objects.select_related("matter"), pk=kwargs["pk"]
            )
            blocked = redirect_if_matter_closed(request, transaction.matter)
            if blocked:
                return blocked
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if transaction_is_locked(self.object):
            messages.error(
                request,
                "This transaction is locked and cannot be edited.",
            )
            return redirect("staff:matter_detail", pk=self.object.matter_id)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["matter"] = self.object.matter
        ctx["is_locked"] = transaction_is_locked(self.object)
        return ctx

    def get_success_url(self):
        return reverse("staff:matter_detail", kwargs={"pk": self.object.matter_id})

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit(
            self.request.user,
            AuditLog.Action.UPDATED,
            AuditLog.EntityType.TRANSACTION,
            self.object.pk,
            self.object.description,
            matter=self.object.matter,
        )
        messages.success(self.request, "Transaction updated successfully.")
        return response


class MatterUpdateView(StaffRequiredMixin, UpdateView):
    model = Matter
    form_class = MatterForm
    template_name = "operations/matters/form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.method in ("GET", "POST"):
            matter = get_object_or_404(Matter, pk=kwargs["pk"])
            blocked = redirect_if_matter_closed(request, matter)
            if blocked:
                return blocked
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, current = matter_workflow_steps(self.object)
        ctx["workflow_steps"] = steps
        ctx["current_step"] = 1
        ctx["wizard_mode"] = False
        return ctx

    def get_success_url(self):
        return reverse("staff:matter_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit(
            self.request.user,
            AuditLog.Action.UPDATED,
            AuditLog.EntityType.MATTER,
            self.object.pk,
            self.object.reference_number,
            matter=self.object,
        )
        messages.success(self.request, "Matter updated successfully.")
        return response


class MatterDocumentsView(StaffRequiredMixin, DetailView):
    model = Matter
    template_name = "operations/matters/documents.html"
    context_object_name = "matter"

    def dispatch(self, request, *args, **kwargs):
        if request.method in ("GET", "POST"):
            matter = get_object_or_404(Matter, pk=kwargs["pk"])
            blocked = redirect_if_matter_closed(request, matter)
            if blocked:
                return blocked
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, current = matter_workflow_steps(self.object)
        ctx["workflow_steps"] = steps
        ctx["current_step"] = 2
        ctx["documents"] = self.object.documents.order_by("-created_at")
        ctx["form"] = DocumentForm()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.matter = self.object
            doc.uploaded_by = request.user
            doc.save()
            log_audit(
                request.user,
                AuditLog.Action.CREATED,
                AuditLog.EntityType.DOCUMENT,
                doc.pk,
                doc.title,
                matter=self.object,
            )
            messages.success(request, "Document added.")
            return redirect("staff:matter_documents", pk=self.object.pk)
        ctx = self.get_context_data()
        ctx["form"] = form
        return render(request, self.template_name, ctx)


class MatterFinancesView(StaffRequiredMixin, DetailView):
    model = Matter
    template_name = "operations/matters/finances.html"
    context_object_name = "matter"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, current = matter_workflow_steps(self.object)
        ctx["workflow_steps"] = steps
        ctx["current_step"] = 3
        ctx["transactions"] = self.object.transactions.order_by("-transaction_date")
        ctx["form"] = TransactionForm(initial={"currency": "USD"})
        summary = matter_finance_summary(self.object)
        ctx.update(summary)
        ctx["matter_is_closed"] = matter_is_closed(self.object)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if matter_is_closed(self.object):
            messages.error(
                request,
                "This matter is closed. New transactions cannot be added.",
            )
            return redirect("staff:matter_finances", pk=self.object.pk)
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.matter = self.object
            txn.recorded_by = request.user
            txn.save()
            log_audit(
                request.user,
                AuditLog.Action.CREATED,
                AuditLog.EntityType.TRANSACTION,
                txn.pk,
                txn.description,
                matter=self.object,
            )
            if auto_complete_matter_if_paid(self.object):
                messages.success(
                    request,
                    "Transaction recorded. Matter automatically marked as completed.",
                )
            else:
                messages.success(request, "Transaction recorded.")
            return redirect("staff:matter_finances", pk=self.object.pk)
        ctx = self.get_context_data()
        ctx["form"] = form
        return render(request, self.template_name, ctx)


class MatterCompleteView(StaffRequiredMixin, DetailView):
    model = Matter
    template_name = "operations/matters/complete.html"
    context_object_name = "matter"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, current = matter_workflow_steps(self.object)
        ctx["workflow_steps"] = steps
        ctx["current_step"] = 4
        ctx["documents"] = self.object.documents.all()
        ctx["transactions"] = self.object.transactions.all()
        ctx["matter_is_closed"] = matter_is_closed(self.object)
        ctx["can_complete"] = can_manually_complete_matter(self.object)
        ctx["document_count"] = ctx["documents"].count()
        ctx["pending_income"] = self.object.transactions.filter(
            transaction_type=Transaction.Type.INCOME,
            status=Transaction.Status.PENDING,
        ).count()
        return ctx

    def post(self, request, *args, **kwargs):
        matter = self.get_object()
        action = request.POST.get("action")
        old_status = matter.status
        if action == "complete":
            if not can_manually_complete_matter(matter):
                messages.error(
                    request,
                    "Cannot complete until all income fees are paid or waived.",
                )
            else:
                apply_matter_status(matter, Matter.Status.COMPLETED)
                log_status_change(
                    request.user,
                    AuditLog.EntityType.MATTER,
                    matter,
                    old_status,
                    Matter.Status.COMPLETED,
                    label=matter.reference_number,
                )
                messages.success(
                    request,
                    f"Matter {matter.reference_number} marked as completed.",
                )
        elif action == "awaiting_payment":
            if matter_is_closed(matter):
                messages.error(request, "This matter is closed.")
            else:
                apply_matter_status(matter, Matter.Status.AWAITING_PAYMENT)
                log_status_change(
                    request.user,
                    AuditLog.EntityType.MATTER,
                    matter,
                    old_status,
                    Matter.Status.AWAITING_PAYMENT,
                    label=matter.reference_number,
                )
                messages.info(request, "Matter set to awaiting payment.")
        elif action == "reopen":
            apply_matter_status(matter, Matter.Status.IN_PROGRESS)
            log_status_change(
                request.user,
                AuditLog.EntityType.MATTER,
                matter,
                old_status,
                Matter.Status.IN_PROGRESS,
                label=matter.reference_number,
            )
            messages.success(request, "Matter reopened for further work.")
        return redirect("staff:matter_detail", pk=matter.pk)


class MatterWizardView(StaffRequiredMixin, View):
    """Three-step wizard: client → matter details → review & create."""

    step_templates = {
        "client": "operations/matters/wizard_client.html",
        "details": "operations/matters/wizard_details.html",
        "review": "operations/matters/wizard_review.html",
    }

    def dispatch(self, request, *args, **kwargs):
        self.step_name = kwargs.get("step", "client")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, step="client"):
        if step == "client":
            clear_wizard_data(request.session)
        if step == "client":
            form = MatterWizardClientForm(initial=get_wizard_data(request.session).get("client", {}))
        elif step == "details":
            if not get_wizard_data(request.session).get("client"):
                return redirect("staff:matter_wizard", step="client")
            form = MatterWizardDetailsForm(initial=get_wizard_data(request.session).get("details", {}))
        elif step == "review":
            data = get_wizard_data(request.session)
            if not data.get("client") or not data.get("details"):
                return redirect("staff:matter_wizard", step="client")
            client = get_object_or_404(Client, pk=data["client"]["client"])
            service = get_object_or_404(ServiceType, pk=data["details"]["service_type"])
            return render(
                request,
                self.step_templates["review"],
                {
                    "client": client,
                    "service": service,
                    "details": data["details"],
                    "wizard_steps": self._wizard_steps(step),
                    "step": step,
                    "step_number": 3,
                    "default_fee": service.default_fee,
                },
            )
        else:
            return redirect("staff:matter_wizard", step="client")
        return render(
            request,
            self.step_templates[step],
            {"form": form, "wizard_steps": self._wizard_steps(step), "step": step, "step_number": self._step_number(step)},
        )

    def post(self, request, step="client"):
        if step == "client":
            form = MatterWizardClientForm(request.POST)
            if form.is_valid():
                data = get_wizard_data(request.session)
                data["client"] = {"client": form.cleaned_data["client"].pk}
                set_wizard_data(request.session, data)
                return redirect("staff:matter_wizard", step="details")
        elif step == "details":
            form = MatterWizardDetailsForm(request.POST)
            if form.is_valid():
                data = get_wizard_data(request.session)
                cleaned = {}
                for key, val in form.cleaned_data.items():
                    cleaned[key] = val.pk if hasattr(val, "pk") else val.isoformat() if hasattr(val, "isoformat") else val
                data["details"] = cleaned
                data["create_fee"] = form.cleaned_data.get("create_fee", False)
                set_wizard_data(request.session, data)
                return redirect("staff:matter_wizard", step="review")
        elif step == "review":
            return self._finalize(request)
        else:
            return redirect("staff:matter_wizard", step="client")

        return render(
            request,
            self.step_templates.get(step, self.step_templates["client"]),
            {"form": form, "wizard_steps": self._wizard_steps(step), "step": step, "step_number": self._step_number(step)},
        )

    def _finalize(self, request):
        data = get_wizard_data(request.session)
        client_id = data.get("client", {}).get("client")
        details = data.get("details", {})
        if not client_id or not details:
            messages.error(request, "Wizard session expired. Please start again.")
            return redirect("staff:matter_wizard", step="client")

        client = get_object_or_404(Client, pk=client_id)
        service = get_object_or_404(ServiceType, pk=details["service_type"])

        from django.utils.dateparse import parse_datetime

        scheduled_at = details.get("scheduled_at")
        if scheduled_at:
            scheduled_at = parse_datetime(scheduled_at)

        matter = Matter.objects.create(
            client=client,
            service_type=service,
            title=details["title"],
            description=details.get("description", ""),
            status=details.get("status", Matter.Status.INQUIRY),
            scheduled_at=scheduled_at,
            assigned_to=request.user,
        )

        if data.get("create_fee") and service.default_fee:
            Transaction.objects.create(
                matter=matter,
                transaction_type=Transaction.Type.INCOME,
                description=f"{service.name} fee",
                amount=service.default_fee,
                currency="USD",
                status=Transaction.Status.PENDING,
                recorded_by=request.user,
            )

        clear_wizard_data(request.session)
        messages.success(request, f"Matter {matter.reference_number} created. Continue with documents and payment.")
        return redirect("staff:matter_documents", pk=matter.pk)

    def _step_number(self, step):
        return {"client": 1, "details": 2, "review": 3}.get(step, 1)

    def _wizard_steps(self, current):
        steps_meta = [
            ("client", _("Client"), _("Select the client")),
            ("details", _("Matter"), _("Service, schedule, and details")),
            ("review", _("Review"), _("Confirm and create")),
        ]
        order = [s[0] for s in steps_meta]
        current_idx = order.index(current) if current in order else 0
        return [
            {
                "number": i + 1,
                "slug": slug,
                "label": label,
                "description": description,
                "active": slug == current,
                "done": i < current_idx,
            }
            for i, (slug, label, description) in enumerate(steps_meta)
        ]


class DocumentListView(StaffRequiredMixin, ListView):
    model = Document
    template_name = "operations/documents/list.html"
    context_object_name = "documents"
    paginate_by = 25

    def get_queryset(self):
        qs = Document.objects.select_related("matter", "matter__client").order_by("-created_at")
        return filter_documents(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Document.Status.choices
        ctx["active_status"] = self.request.GET.get("status", "")
        ctx["filters"] = self.request.GET
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_query"] = params.urlencode()
        return ctx


class TransactionListView(StaffRequiredMixin, ListView):
    model = Transaction
    template_name = "operations/transactions/list.html"
    context_object_name = "transactions"
    paginate_by = 25

    def get_queryset(self):
        qs = Transaction.objects.select_related("matter", "matter__client").order_by(
            "-transaction_date", "-created_at"
        )
        return filter_transactions(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(global_finance_summary())
        ctx["status_choices"] = Transaction.Status.choices
        ctx["type_choices"] = Transaction.Type.choices
        ctx["payment_method_choices"] = Transaction.PaymentMethod.choices
        ctx["active_status"] = self.request.GET.get("status", "")
        ctx["active_type"] = self.request.GET.get("type", "")
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["filter_query"] = params.urlencode()
        ctx["filters"] = self.request.GET
        ctx["clear_url"] = reverse("staff:transaction_list")
        return ctx


class TransactionReceiptView(StaffRequiredMixin, DetailView):
    model = Transaction
    template_name = "operations/print/receipt.html"
    context_object_name = "transaction"

    def get_queryset(self):
        return Transaction.objects.select_related(
            "matter",
            "matter__client",
            "matter__service_type",
            "recorded_by",
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.GET.get("format") == "pdf":
            context = self.get_context_data(object=self.object)
            filename = f"receipt-{self.object.pk}.pdf"
            pdf = render_pdf_response(self.template_name, context, filename=filename)
            if pdf:
                return pdf
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["matter"] = self.object.matter
        return ctx


class MatterDocumentsPrintView(StaffRequiredMixin, DetailView):
    model = Matter
    template_name = "operations/print/matter_documents.html"
    context_object_name = "matter"

    def get_queryset(self):
        return Matter.objects.select_related("client", "service_type")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["documents"] = self.object.documents.order_by("title")
        ctx["transactions"] = self.object.transactions.order_by("-transaction_date")
        return ctx


class CalendarView(StaffRequiredMixin, TemplateView):
    template_name = "operations/calendar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        week_param = self.request.GET.get("week")
        if week_param:
            try:
                week_start = date.fromisoformat(week_param)
            except ValueError:
                week_start = today - timedelta(days=today.weekday())
        else:
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)
        week_days = [week_start + timedelta(days=i) for i in range(7)]

        matters = (
            Matter.objects.filter(
                scheduled_at__date__gte=week_start,
                scheduled_at__date__lte=week_end,
            )
            .exclude(status=Matter.Status.CANCELLED)
            .select_related("client", "service_type", "assigned_to")
            .order_by("scheduled_at")
        )

        by_day = {day: [] for day in week_days}
        for matter in matters:
            if matter.scheduled_at:
                by_day[matter.scheduled_at.date()].append(matter)

        ctx["week_days"] = [{"date": day, "matters": by_day[day]} for day in week_days]
        ctx["week_start"] = week_start
        ctx["week_end"] = week_end
        ctx["prev_week"] = (week_start - timedelta(days=7)).isoformat()
        ctx["next_week"] = (week_start + timedelta(days=7)).isoformat()
        ctx["today"] = today
        return ctx


class AuditLogListView(ManagerRequiredMixin, ListView):
    model = AuditLog
    template_name = "operations/audit/list.html"
    context_object_name = "entries"
    paginate_by = 40

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user", "matter").order_by("-created_at")
        entity = self.request.GET.get("entity")
        if entity in AuditLog.EntityType.values:
            qs = qs.filter(entity_type=entity)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["entity_types"] = AuditLog.EntityType.choices
        ctx["active_entity"] = self.request.GET.get("entity", "")
        return ctx


class StaffProfileView(StaffRequiredMixin, UpdateView):
    form_class = UserProfileForm
    template_name = "operations/profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("staff:profile")

    def form_valid(self, form):
        messages.success(self.request, _("Profile updated successfully."))
        return super().form_valid(form)


class AppointmentListView(StaffRequiredMixin, ListView):
    model = AppointmentRequest
    template_name = "operations/appointments/list.html"
    context_object_name = "appointments"
    paginate_by = 25

    def get_queryset(self):
        qs = AppointmentRequest.objects.order_by("-created_at")
        status = self.request.GET.get("status")
        if status in AppointmentRequest.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = AppointmentRequest.Status.choices
        ctx["active_status"] = self.request.GET.get("status", "")
        ctx["pending_count"] = AppointmentRequest.objects.filter(
            status=AppointmentRequest.Status.PENDING
        ).count()
        return ctx

    def post(self, request, *args, **kwargs):
        appointment = get_object_or_404(AppointmentRequest, pk=request.POST.get("pk"))
        status = request.POST.get("status")
        if status in AppointmentRequest.Status.values:
            appointment.status = status
            appointment.save(update_fields=["status", "updated_at"])
            messages.success(request, _("Appointment updated."))
        return redirect("staff:appointment_list")
