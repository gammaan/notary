from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client as HttpClient, TestCase
from django.urls import reverse

from operations.models import Client, Document, Matter, ServiceType, Transaction
from operations.utils import safe_redirect

User = get_user_model()


class StaffPortalTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="securepass123",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        self.client_obj = Client.objects.create(first_name="Ali", last_name="Hassan")
        self.service = ServiceType.objects.create(name="Notarization", default_fee=Decimal("50"))
        self.matter = Matter.objects.create(
            client=self.client_obj,
            service_type=self.service,
            title="Property sale",
        )
        self.http = HttpClient()
        self.http.login(email="staff@example.com", password="securepass123")

    def test_document_download_requires_staff(self):
        doc = Document.objects.create(
            matter=self.matter,
            title="Contract",
            file=SimpleUploadedFile("contract.pdf", b"%PDF-1.4 test"),
            uploaded_by=self.staff,
        )
        anon = HttpClient()
        url = reverse("staff:document_download", kwargs={"pk": doc.pk})
        self.assertEqual(anon.get(url).status_code, 302)
        response = self.http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_closed_matter_blocks_document_upload(self):
        self.matter.status = Matter.Status.COMPLETED
        self.matter.save()
        url = reverse("staff:matter_documents", kwargs={"pk": self.matter.pk})
        response = self.http.get(url)
        self.assertRedirects(response, reverse("staff:matter_detail", kwargs={"pk": self.matter.pk}))

    def test_safe_redirect_blocks_external_url(self):
        request = self.http.get("/").wsgi_request
        request.META["HTTP_HOST"] = "testserver"
        response = safe_redirect(
            request,
            "https://evil.example/phish",
            "staff:dashboard",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("staff:dashboard"))

    def test_locked_transaction_blocks_edit_post(self):
        txn = Transaction.objects.create(
            matter=self.matter,
            transaction_type=Transaction.Type.INCOME,
            description="Fee",
            amount=Decimal("50"),
            status=Transaction.Status.PAID,
            recorded_by=self.staff,
        )
        url = reverse("staff:transaction_edit", kwargs={"pk": txn.pk})
        response = self.http.post(url, {"description": "Changed"})
        self.assertRedirects(response, reverse("staff:matter_detail", kwargs={"pk": self.matter.pk}))
