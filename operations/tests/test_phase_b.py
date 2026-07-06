from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client as HttpClient, TestCase
from django.urls import reverse

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
        self.client_obj = Client.objects.create(first_name="Ali", last_name="Hassan")
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
        url = reverse("staff:document_action", kwargs={"pk": self.document.pk})
        response = client.post(url, {"action": "delete", "next": reverse("staff:matter_detail", kwargs={"pk": self.matter.pk})})
        self.assertTrue(Document.objects.filter(pk=self.document.pk).exists())

    def test_manager_can_delete_document(self):
        client = HttpClient()
        client.login(email="manager@example.com", password="securepass123")
        url = reverse("staff:document_action", kwargs={"pk": self.document.pk})
        client.post(url, {"action": "delete", "next": reverse("staff:matter_detail", kwargs={"pk": self.matter.pk})})
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
        self.client_obj = Client.objects.create(first_name="Ali", last_name="Hassan")
        self.service = ServiceType.objects.create(name="Notarization")

    def test_calendar_page_loads(self):
        client = HttpClient()
        client.login(email="staff@example.com", password="securepass123")
        response = client.get(reverse("staff:calendar"))
        self.assertEqual(response.status_code, 200)
