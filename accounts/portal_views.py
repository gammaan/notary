from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView

from accounts.models import User
from operations.models import Client, Matter


class ClientRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "/account/login/"

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and not user.is_staff and self.get_client() is not None

    def get_client(self):
        if hasattr(self, "_portal_client"):
            return self._portal_client
        user = self.request.user
        client = Client.objects.filter(user=user, is_active=True).first()
        if not client and user.email:
            client = Client.objects.filter(email__iexact=user.email, is_active=True).first()
            if client and not client.user_id:
                client.user = user
                client.save(update_fields=["user", "updated_at"])
        self._portal_client = client
        return client

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["portal_client"] = self.get_client()
        return ctx


class PortalDashboardView(ClientRequiredMixin, TemplateView):
    template_name = "portal/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = self.get_client()
        ctx["matters"] = (
            Matter.objects.filter(client=client)
            .select_related("service_type")
            .order_by("-created_at")
        )
        return ctx


class PortalMatterDetailView(ClientRequiredMixin, DetailView):
    model = Matter
    template_name = "portal/matter_detail.html"
    context_object_name = "matter"

    def get_queryset(self):
        return Matter.objects.filter(client=self.get_client()).select_related(
            "service_type", "assigned_to"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["documents"] = self.object.documents.exclude(status="archived").order_by("-created_at")
        ctx["transactions"] = self.object.transactions.filter(
            transaction_type="income"
        ).order_by("-transaction_date")
        return ctx
