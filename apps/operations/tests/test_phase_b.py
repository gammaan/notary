from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client as HttpClient, TestCase
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta

from operations.models import AuditLog, Client, Document, Matter, ServiceType, Transaction

User = get_user_model()


class StaffPermissionsTests(TestCase):
    def setUp(self):
        self.clerk = User.objects.create_user(
            email="clerk@example.com",
            password="securepass123",
            first_name="Clerk",
            last_name="User",
            is_staff=True,
            role=User.Role.STAFF,
        )
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="securepass123",
            first_name="Manager",
            last_name="User",
            is_staff=True,
            role=User.Role.MANAGER,
        )
        self.client_obj = Client.objects.create(full_name="Ali Hassan")
        self.service = ServiceType.objects.create(name="Notarization")
        self.matter = Matter.objects.create(
            client=self.client_obj,
            service_type=self.service,
            title="Test",
        )
        self.document = Document.objects.create(
            matter=self.matter,
            title="Contract",
            uploaded_by=self.manager,
        )

    def test_clerk_cannot_delete_document(self):
        client = HttpClient()
        client.login(email="clerk@example.com", password="securepass123")
        url = reverse("staff:document_action", kwargs={"pk": self.document.uuid})
        response = client.post(url, {"action": "delete", "next": reverse("staff:matter_detail", kwargs={"pk": self.matter.uuid})})
        self.assertTrue(Document.objects.filter(pk=self.document.pk).exists())

    def test_manager_can_delete_document(self):
        client = HttpClient()
        client.login(email="manager@example.com", password="securepass123")
        url = reverse("staff:document_action", kwargs={"pk": self.document.uuid})
        client.post(url, {"action": "delete", "next": reverse("staff:matter_detail", kwargs={"pk": self.matter.uuid})})
        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())
        self.assertTrue(AuditLog.objects.filter(entity_type=AuditLog.EntityType.DOCUMENT, action=AuditLog.Action.DELETED).exists())

    def test_clerk_cannot_view_audit_log(self):
        client = HttpClient()
        client.login(email="clerk@example.com", password="securepass123")
        response = client.get(reverse("staff:audit_log"))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_view_audit_log(self):
        client = HttpClient()
        client.login(email="manager@example.com", password="securepass123")
        response = client.get(reverse("staff:audit_log"))
        self.assertEqual(response.status_code, 200)


class CalendarTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="securepass123",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        self.client_obj = Client.objects.create(full_name="Ali Hassan")
        self.service = ServiceType.objects.create(name="Notarization")

    def test_calendar_page_loads(self):
        client = HttpClient()
        client.login(email="staff@example.com", password="securepass123")
        response = client.get(reverse("staff:calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "staff-calendar-grid")

    def test_calendar_date_filter_expands_day(self):
        client = HttpClient()
        client.login(email="staff@example.com", password="securepass123")
        scheduled = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        for index in range(6):
            Matter.objects.create(
                title=f"Matter {index}",
                client=self.client_obj,
                service_type=self.service,
                status=Matter.Status.SCHEDULED,
                scheduled_at=scheduled + timedelta(hours=index),
            )
        day = scheduled.date().isoformat()
        response = client.get(reverse("staff:calendar"), {"date": day})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "is-expanded")
        self.assertNotContains(response, "See 2 more")
