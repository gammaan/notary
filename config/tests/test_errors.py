from django.test import Client, TestCase, override_settings
from django.urls import reverse

from config.views import page_not_found, server_error


@override_settings(DEBUG=False)
class ErrorPageTests(TestCase):
    def test_public_404_page(self):
        response = Client().get("/en/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, "Back to home", status_code=404)

    def test_staff_404_page(self):
        response = Client().get("/en/staff/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, "Back to dashboard", status_code=404)

    def test_server_error_view(self):
        request = Client().get("/en/").wsgi_request
        response = server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Server error", status_code=500)

    def test_page_not_found_view(self):
        request = Client().get("/en/missing/").wsgi_request
        response = page_not_found(request, Exception("missing"))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "404", status_code=404)
