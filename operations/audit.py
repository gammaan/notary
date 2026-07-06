"""Record staff actions for compliance and review."""

from operations.models import AuditLog


def log_audit(user, action, entity_type, entity_id, entity_label, *, detail="", matter=None):
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_label=entity_label[:255],
        detail=detail[:500],
        matter=matter,
    )


def log_status_change(user, entity_type, obj, old_status, new_status, *, matter=None, label=None):
    entity_label = label or str(obj)
    log_audit(
        user,
        AuditLog.Action.STATUS_CHANGED,
        entity_type,
        obj.pk,
        entity_label,
        detail=f"{old_status} → {new_status}",
        matter=matter,
    )
