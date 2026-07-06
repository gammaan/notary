"""CMS content helpers for public pages."""

from cms.models import PortfolioItem, Post

FEATURED_LIMIT = 3


def featured_posts(limit=FEATURED_LIMIT):
    qs = Post.objects.filter(status=Post.Status.PUBLISHED, is_featured=True).order_by(
        "-published_at", "-created_at"
    )[:limit]
    if qs:
        return qs
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by(
        "-published_at", "-created_at"
    )[:limit]


def featured_portfolio(limit=FEATURED_LIMIT):
    qs = PortfolioItem.objects.filter(
        status=PortfolioItem.Status.PUBLISHED,
        is_featured=True,
    ).order_by("sort_order", "-published_at")[:limit]
    if qs:
        return qs
    return PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED).order_by(
        "sort_order", "-published_at"
    )[:limit]
