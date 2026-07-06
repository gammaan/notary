from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from cms.models import PortfolioItem, Post
from pages.seo import page_seo


def blog_list(request):
    posts = Post.objects.filter(status=Post.Status.PUBLISHED)
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
            title=_("News & updates | Himilo Notary"),
            description=_("Latest news, notices, and articles from Himilo Notary."),
            path=request.path,
        )
    )
    return render(request, "cms/blog_list.html", ctx)


def blog_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    related = (
        Post.objects.filter(status=Post.Status.PUBLISHED, category=post.category)
        .exclude(pk=post.pk)[:3]
    )
    ctx = {"post": post, "related_posts": related}
    ctx.update(
        page_seo(
            request,
            title=f"{post.title} | Himilo Notary",
            description=post.summary or post.title,
            path=request.path,
        )
    )
    return render(request, "cms/blog_detail.html", ctx)


def portfolio_list(request):
    items = PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED)
    ctx = {"portfolio_items": items}
    ctx.update(
        page_seo(
            request,
            title=_("Portfolio | Himilo Notary"),
            description=_("Examples of notarial work handled by Himilo Notary."),
            path=request.path,
        )
    )
    return render(request, "cms/portfolio_list.html", ctx)


def portfolio_detail(request, slug):
    item = get_object_or_404(PortfolioItem, slug=slug, status=PortfolioItem.Status.PUBLISHED)
    related = (
        PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED)
        .exclude(pk=item.pk)[:3]
    )
    ctx = {"item": item, "related_items": related}
    ctx.update(
        page_seo(
            request,
            title=f"{item.title} | Himilo Notary",
            description=item.summary[:500],
            path=request.path,
        )
    )
    return render(request, "cms/portfolio_detail.html", ctx)
