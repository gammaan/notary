from accounts.permissions import can_delete_records, can_view_audit_log


def staff_permissions(request):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return {}
    return {
        "staff_can_delete": can_delete_records(user),
        "staff_can_view_audit": can_view_audit_log(user),
    }
