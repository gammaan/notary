from django.test import Client as HttpClient, TestCase
from django.urls import reverse

from cms.models import Post


class CmsLocaleTests(TestCase):
    def test_posts_filtered_by_language(self):
        Post.objects.create(
            title="English post",
            body="Body",
            status=Post.Status.PUBLISHED,
            language="en",
        )
        Post.objects.create(
            title="Somali post",
            body="Body",
            language="so",
            status=Post.Status.PUBLISHED,
        )
        client = HttpClient()
        response = client.get("/so/news/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Somali post")
        self.assertNotContains(response, "English post")
