from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone

from accounts.permissions import can_delete_records, can_view_audit_log


class UUIDSlugMixin:
    pk_url_kwarg = None
    slug_field = "uuid"
    slug_url_kwarg = "pk"


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "/staff/login/"

    def test_func(self):
        return self.request.user.is_staff


class ManagerRequiredMixin(StaffRequiredMixin):
    def test_func(self):
        return can_view_audit_log(self.request.user)


class StaffListPrintMixin:
    """Print-friendly list view: applies list filters without pagination."""

    def paginate_queryset(self, queryset, page_size):
        return (None, None, queryset, False)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["printed_at"] = timezone.now()
        items = ctx.get(self.context_object_name, [])
        ctx["record_count"] = items.count() if hasattr(items, "count") else len(items)
        params = self.request.GET.copy()
        ctx["filter_query"] = params.urlencode()
        return ctx


def deny_delete_if_needed(request, message="Only managers can delete records."):
    if can_delete_records(request.user):
        return None
    from django.contrib import messages
    from django.shortcuts import redirect

    messages.error(request, message)
    return redirect(request.META.get("HTTP_REFERER", "/staff/"))
