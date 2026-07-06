from decimal import Decimal

from django.test import TestCase

from operations.models import Client, Matter, ServiceType, Transaction
from operations.transaction_rules import (
    auto_complete_matter_if_paid,
    can_manually_complete_matter,
    finance_step_done,
    matter_finances_settled,
    matter_is_closed,
)


class TransactionRulesTests(TestCase):
    def setUp(self):
        self.client = Client.objects.create(first_name="A", last_name="B")
        self.service = ServiceType.objects.create(name="Notarization", default_fee=Decimal("50"))
        self.matter = Matter.objects.create(
            client=self.client,
            service_type=self.service,
            title="Test matter",
        )

    def test_finance_step_done_when_no_income(self):
        self.assertFalse(finance_step_done(self.matter))
        self.assertTrue(can_manually_complete_matter(self.matter))

    def test_finance_step_done_when_all_settled(self):
        Transaction.objects.create(
            matter=self.matter,
            transaction_type=Transaction.Type.INCOME,
            description="Fee",
            amount=Decimal("50"),
            status=Transaction.Status.PAID,
        )
        self.assertTrue(matter_finances_settled(self.matter))
        self.assertTrue(finance_step_done(self.matter))
        self.assertTrue(can_manually_complete_matter(self.matter))

    def test_auto_complete_when_paid(self):
        Transaction.objects.create(
            matter=self.matter,
            transaction_type=Transaction.Type.INCOME,
            description="Fee",
            amount=Decimal("50"),
            status=Transaction.Status.PAID,
        )
        self.assertTrue(auto_complete_matter_if_paid(self.matter))
        self.matter.refresh_from_db()
        self.assertTrue(matter_is_closed(self.matter))

    def test_cannot_complete_with_pending_fee(self):
        Transaction.objects.create(
            matter=self.matter,
            transaction_type=Transaction.Type.INCOME,
            description="Fee",
            amount=Decimal("50"),
            status=Transaction.Status.PENDING,
        )
        self.assertFalse(can_manually_complete_matter(self.matter))
