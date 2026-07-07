from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from cms.locale import filter_by_language, request_language
from cms.models import PortfolioItem, Post
from pages.seo import page_seo


def _get_post(slug, language):
    try:
        return Post.objects.get(slug=slug, status=Post.Status.PUBLISHED, language=language)
    except Post.DoesNotExist:
        if language != "en":
            return get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED, language="en")
        raise


def _get_portfolio_item(slug, language):
    try:
        return PortfolioItem.objects.get(
            slug=slug, status=PortfolioItem.Status.PUBLISHED, language=language
        )
    except PortfolioItem.DoesNotExist:
        if language != "en":
            return get_object_or_404(
                PortfolioItem,
                slug=slug,
                status=PortfolioItem.Status.PUBLISHED,
                language="en",
            )
        raise


def blog_list(request):
    language = request_language(request)
    posts = filter_by_language(
        Post.objects.filter(status=Post.Status.PUBLISHED),
        language,
    )
    category = request.GET.get("category")
    if category in Post.Category.values:
        posts = posts.filter(category=category)

    ctx = {
        "posts": posts,
        "active_category": category,
        "categories": Post.Category.choices,
    }
    ctx.update(
        page_seo(
            request,
            title=_("News & updates | Notaria Notary"),
            description=_("Latest news, notices, and articles from Notaria Notary."),
            path=request.path,
        )
    )
    return render(request, "cms/blog_list.html", ctx)


def blog_detail(request, slug):
    language = request_language(request)
    post = _get_post(slug, language)
    related = (
        filter_by_language(
            Post.objects.filter(status=Post.Status.PUBLISHED, category=post.category),
            language,
            fallback=False,
        )
        .exclude(pk=post.pk)[:3]
    )
    ctx = {"post": post, "related_posts": related}
    ctx.update(
        page_seo(
            request,
            title=f"{post.title} | Notaria Notary",
            description=post.summary or post.title,
            path=request.path,
        )
    )
    return render(request, "cms/blog_detail.html", ctx)


def portfolio_list(request):
    language = request_language(request)
    items = filter_by_language(
        PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED),
        language,
    )
    ctx = {"portfolio_items": items}
    ctx.update(
        page_seo(
            request,
            title=_("Portfolio | Notaria Notary"),
            description=_("Examples of notarial work handled by Notaria Notary."),
            path=request.path,
        )
    )
    return render(request, "cms/portfolio_list.html", ctx)


def portfolio_detail(request, slug):
    language = request_language(request)
    item = _get_portfolio_item(slug, language)
    related = (
        filter_by_language(
            PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED),
            language,
            fallback=False,
        )
        .exclude(pk=item.pk)[:3]
    )
    ctx = {"item": item, "related_items": related}
    ctx.update(
        page_seo(
            request,
            title=f"{item.title} | Notaria Notary",
            description=item.summary[:500],
            path=request.path,
        )
    )
    return render(request, "cms/portfolio_detail.html", ctx)
