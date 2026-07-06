"""CMS content helpers for public pages."""

from cms.locale import filter_by_language
from cms.models import PortfolioItem, Post

FEATURED_LIMIT = 3


def featured_posts(language="en", limit=FEATURED_LIMIT):
    base = Post.objects.filter(status=Post.Status.PUBLISHED)
    qs = filter_by_language(base.filter(is_featured=True), language)[:limit]
    if qs:
        return qs
    return filter_by_language(base, language).order_by("-published_at", "-created_at")[:limit]


def featured_portfolio(language="en", limit=FEATURED_LIMIT):
    base = PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED)
    qs = filter_by_language(base.filter(is_featured=True), language).order_by(
        "sort_order", "-published_at"
    )[:limit]
    if qs:
        return qs
    return filter_by_language(base, language).order_by("sort_order", "-published_at")[:limit]
