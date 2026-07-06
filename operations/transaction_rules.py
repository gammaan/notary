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

REOPEN_STATUSES = frozenset(
    {
        Matter.Status.INQUIRY,
        Matter.Status.SCHEDULED,
        Matter.Status.IN_PROGRESS,
        Matter.Status.AWAITING_PAYMENT,
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


def finance_step_done(matter):
    """Workflow step 3: all income fees paid or waived."""
    return matter_finances_settled(matter)


def can_manually_complete_matter(matter):
    """Allow staff to mark complete when finances are settled or no fees exist."""
    income = matter.transactions.filter(transaction_type=Transaction.Type.INCOME)
    if not income.exists():
        return True
    return matter_finances_settled(matter)


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


def apply_matter_status(matter, new_status):
    """Update matter status with completed_at handling."""
    matter.status = new_status
    if new_status == Matter.Status.COMPLETED and not matter.completed_at:
        matter.completed_at = timezone.now()
    elif new_status != Matter.Status.COMPLETED:
        matter.completed_at = None
    matter.save(update_fields=["status", "completed_at", "updated_at"])

