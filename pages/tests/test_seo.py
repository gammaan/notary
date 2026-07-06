from django.test import Client, TestCase, override_settings
from django.urls import reverse

from cms.featured import featured_portfolio, featured_posts
from cms.models import PortfolioItem, Post


class FeaturedContentTests(TestCase):
    def test_featured_posts_prefers_flagged(self):
        Post.objects.create(title="Regular", body="Body", status=Post.Status.PUBLISHED, language="en")
        featured = Post.objects.create(
            title="Featured",
            body="Body",
            status=Post.Status.PUBLISHED,
            is_featured=True,
            language="en",
        )
        results = list(featured_posts(limit=1))
        self.assertEqual(results[0].pk, featured.pk)

    def test_featured_portfolio_fallback(self):
        PortfolioItem.objects.create(
            title="Sample",
            summary="Summary text",
            status=PortfolioItem.Status.PUBLISHED,
            language="en",
        )
        self.assertEqual(featured_portfolio().count(), 1)


class SeoTests(TestCase):
    def test_sitemap_returns_xml(self):
        response = Client().get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])

    @override_settings(DEBUG=True)
    def test_robots_txt_in_debug_disallows(self):
        response = Client().get(reverse("robots"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Disallow: /", response.content)

    def test_privacy_page_renders(self):
        response = Client().get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Privacy Policy")
