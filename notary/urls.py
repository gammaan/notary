from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from cms.views import blog_detail, blog_list, portfolio_detail, portfolio_list
from notary.sitemaps import PortfolioSitemap, PostSitemap, StaticViewSitemap
from pages.robots import robots_txt
from pages.views import home, privacy, terms

sitemaps = {
    "static": StaticViewSitemap,
    "posts": PostSitemap,
    "portfolio": PortfolioSitemap,
}

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

urlpatterns += i18n_patterns(
    path("", home, name="home"),
    path("privacy/", privacy, name="privacy"),
    path("terms/", terms, name="terms"),
    path("staff/", include("operations.urls")),
    path("news/", blog_list, name="blog_list"),
    path("news/<slug:slug>/", blog_detail, name="blog_detail"),
    path("portfolio/", portfolio_list, name="portfolio_list"),
    path("portfolio/<slug:slug>/", portfolio_detail, name="portfolio_detail"),
    path("admin/", admin.site.urls),
    prefix_default_language=True,
)

admin.site.site_header = "Himilo Notary"
admin.site.site_title = "Himilo Notary"
admin.site.index_title = "Dashboard"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

