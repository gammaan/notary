from django.contrib.auth import get_user_model

User = get_user_model()


def is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return getattr(user, "role", None) == User.Role.MANAGER


def is_staff_member(user):
    return user.is_authenticated and user.is_staff


def can_delete_records(user):
    return is_manager(user)


def can_view_audit_log(user):
    return is_manager(user)
