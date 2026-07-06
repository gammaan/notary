from django.urls import reverse
from django.contrib.sitemaps import Sitemap

from cms.models import PortfolioItem, Post

class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return ["home", "blog_list", "portfolio_list", "privacy", "terms"]

    def location(self, item):
        return reverse(item)

class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Post.objects.filter(status=Post.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("blog_detail", kwargs={"slug": obj.slug})

class PortfolioSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return PortfolioItem.objects.filter(status=PortfolioItem.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("portfolio_detail", kwargs={"slug": obj.slug})
