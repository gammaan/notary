"""Business rules for payments and matter completion."""

from django.utils import timezone

from operations.models import Matter, Transaction

LOCKED_TRANSACTION_STATUSES = frozenset(
    {
        Transaction.Status.PAID,
        Transaction.Status.WAIVED,
        Transaction.Status.CANCELLED,
    }
)

SETTLED_TRANSACTION_STATUSES = frozenset(
    {
        Transaction.Status.PAID,
        Transaction.Status.WAIVED,
    }
)


def transaction_is_locked(transaction):
    return transaction.status in LOCKED_TRANSACTION_STATUSES


def matter_is_closed(matter):
    return matter.status in {Matter.Status.COMPLETED, Matter.Status.CANCELLED}


def matter_finances_settled(matter):
    income = matter.transactions.filter(transaction_type=Transaction.Type.INCOME)
    if not income.exists():
        return False
    return not income.exclude(status__in=SETTLED_TRANSACTION_STATUSES).exists()


def auto_complete_matter_if_paid(matter):
    """Mark matter completed when all income fees are paid or waived."""
    if matter_is_closed(matter):
        return False
    if not matter_finances_settled(matter):
        return False
    matter.status = Matter.Status.COMPLETED
    if not matter.completed_at:
        matter.completed_at = timezone.now()
    matter.save(update_fields=["status", "completed_at", "updated_at"])
    return True
