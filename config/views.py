from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _


def health_check(request):
    """Lightweight health endpoint for load balancers and uptime monitors."""
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse(
        {"status": "ok" if db_ok else "degraded", "database": db_ok},
        status=status,
    )


def _is_staff_request(request):
    return "/staff/" in request.path


def _error_page(request, status, title, message):
    is_staff = _is_staff_request(request)
    return render(
        request,
        "errors/page.html",
        {
            "base_template": "core/base_admin.html"
            if is_staff
            else "core/base_public.html",
            "is_staff_error": is_staff,
            "error_code": status,
            "error_title": title,
            "error_message": message,
        },
        status=status,
    )


def bad_request(request, exception):
    return _error_page(
        request,
        400,
        _("Bad request"),
        _("The request could not be understood. Please check and try again."),
    )


def permission_denied(request, exception):
    return _error_page(
        request,
        403,
        _("Access denied"),
        _("You do not have permission to view this page."),
    )


def page_not_found(request, exception):
    return _error_page(
        request,
        404,
        _("Page not found"),
        _("The page you requested does not exist or may have been moved."),
    )


def server_error(request):
    return _error_page(
        request,
        500,
        _("Server error"),
        _("Something went wrong on our end. Please try again in a moment."),
    )
