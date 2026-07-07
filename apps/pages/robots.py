from django.http import HttpResponse
from django.urls import reverse

from django.conf import settings


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
    ]
    if getattr(settings, "DEBUG", False):
        lines = ["User-agent: *", "Disallow: /"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
