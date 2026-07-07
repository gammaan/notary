from django.conf import settings
from django.urls import reverse


def absolute_url(request, path):
    """Build an absolute URL for the current site."""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = getattr(settings, "SITE_URL", "").rstrip("/")
    if base:
        return f"{base}{path}"
    return request.build_absolute_uri(path)


def page_seo(request, *, title, description, path="/", image=None):
    """Standard SEO context for public templates."""
    return {
        "seo_title": title,
        "seo_description": description,
        "seo_url": absolute_url(request, path),
        "seo_image": image,
    }
