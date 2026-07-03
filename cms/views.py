from django.shortcuts import get_object_or_404, render

from cms.models import PortfolioItem, Post


def blog_list(request):
    posts = Post.objects.filter(status=Post.Status.PUBLISHED)
    category = request.GET.get("category")
    if category in Post.Category.values:
        posts = posts.filter(category=category)

    return render(
        request,
        "cms/blog_list.html",
        {
            "posts": posts,
            "active_category": category,
            "categories": Post.Category.choices,
        },
    )


def blog_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    related = (
        Post.objects.filter(status=Post.Status.PUBLISHED, category=post.category)
        .exclude(pk=post.pk)[:3]
    )
    return render(
        request,
        "cms/blog_detail.html",
        {"post": post, "related_posts": related},
    )


def portfolio_list(request):
    items = PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED)
    return render(request, "cms/portfolio_list.html", {"portfolio_items": items})


def portfolio_detail(request, slug):
    item = get_object_or_404(PortfolioItem, slug=slug, status=PortfolioItem.Status.PUBLISHED)
    related = (
        PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED)
        .exclude(pk=item.pk)[:3]
    )
    return render(
        request,
        "cms/portfolio_detail.html",
        {"item": item, "related_items": related},
    )
