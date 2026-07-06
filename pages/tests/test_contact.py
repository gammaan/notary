from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(
    CONTACT_EMAIL="office@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ContactFormTests(TestCase):
    def test_contact_form_sends_email(self):
        client = Client()
        url = reverse("home")
        response = client.post(
            url,
            {
                "form_type": "contact",
                "name": "Jane Doe",
                "email": "jane@example.com",
                "service": "General notarization",
                "message": "Need an appointment next week.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Jane Doe", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["office@example.com"])

    def test_contact_form_rejects_invalid_email(self):
        client = Client()
        url = reverse("home")
        response = client.post(
            url,
            {
                "form_type": "contact",
                "name": "Jane Doe",
                "email": "not-an-email",
                "service": "General notarization",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
