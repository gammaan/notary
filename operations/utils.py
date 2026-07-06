"""Shared helpers for staff portal views."""

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from operations.transaction_rules import matter_is_closed


def safe_redirect(request, next_url, default_name, **default_kwargs):
    """Redirect only to same-host URLs."""
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(default_name, **default_kwargs)


def redirect_if_matter_closed(request, matter):
    if matter_is_closed(matter):
        messages.error(request, "This matter is closed and cannot be modified.")
        return redirect("staff:matter_detail", pk=matter.pk)
    return None
