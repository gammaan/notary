"""Finance aggregation helpers."""

from decimal import Decimal

from django.db.models import Sum

from operations.models import Transaction


def matter_finance_summary(matter):
    txns = matter.transactions.all()
    income_qs = txns.filter(transaction_type=Transaction.Type.INCOME)
    expense_qs = txns.filter(transaction_type=Transaction.Type.EXPENSE)

    total_income = income_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    total_expenses = expense_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    total_paid = (
        income_qs.filter(status=Transaction.Status.PAID).aggregate(s=Sum("amount"))["s"]
        or Decimal("0")
    )
    total_expenses_paid = (
        expense_qs.filter(status=Transaction.Status.PAID).aggregate(s=Sum("amount"))["s"]
        or Decimal("0")
    )

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_paid": total_paid,
        "total_expenses_paid": total_expenses_paid,
        "net_income": total_paid - total_expenses_paid,
        "outstanding_income": total_income - total_paid,
    }


def global_finance_summary(queryset=None):
    qs = queryset or Transaction.objects.all()
    matter_qs = qs.filter(matter__isnull=False)
    general_qs = qs.filter(matter__isnull=True)

    def _paid_sum(sub_qs, txn_type):
        return (
            sub_qs.filter(
                transaction_type=txn_type,
                status=Transaction.Status.PAID,
            ).aggregate(s=Sum("amount"))["s"]
            or Decimal("0")
        )

    income_paid = _paid_sum(qs, Transaction.Type.INCOME)
    expenses_paid = _paid_sum(qs, Transaction.Type.EXPENSE)
    matter_income_paid = _paid_sum(matter_qs, Transaction.Type.INCOME)
    matter_expenses_paid = _paid_sum(matter_qs, Transaction.Type.EXPENSE)
    general_income_paid = _paid_sum(general_qs, Transaction.Type.INCOME)
    general_expenses_paid = _paid_sum(general_qs, Transaction.Type.EXPENSE)

    return {
        "income_paid": income_paid,
        "expenses_paid": expenses_paid,
        "net": income_paid - expenses_paid,
        "matter_income_paid": matter_income_paid,
        "matter_expenses_paid": matter_expenses_paid,
        "general_income_paid": general_income_paid,
        "general_expenses_paid": general_expenses_paid,
    }
