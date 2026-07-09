from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from cms.views import blog_detail, blog_list, portfolio_detail, portfolio_list
from config.views import health_check
from config.sitemaps import PortfolioSitemap, PostSitemap, StaticViewSitemap
from pages.robots import robots_txt
from pages.views import home, privacy, profile_page, terms
sitemaps = {
    "static": StaticViewSitemap,
    "posts": PostSitemap,
    "portfolio": PortfolioSitemap,
}

urlpatterns = [
    path("health/", health_check, name="health"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

urlpatterns += i18n_patterns(
    path("", home, name="home"),
    path("privacy/", privacy, name="privacy"),
    path("terms/", terms, name="terms"),
    path("profile/", profile_page, name="profile"),
    path("account/", include("accounts.urls")),
    path("portal/", include("accounts.portal_urls")),
    path("staff/", include("operations.urls")),
    path("news/", blog_list, name="blog_list"),
    path("news/<slug:slug>/", blog_detail, name="blog_detail"),
    path("portfolio/", portfolio_list, name="portfolio_list"),
    path("portfolio/<slug:slug>/", portfolio_detail, name="portfolio_detail"),
    path("admin/", admin.site.urls),
    prefix_default_language=True,
)

admin.site.site_header = "Notaria Notary"
admin.site.site_title = "Notaria Notary"
admin.site.index_title = "Dashboard"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = "config.views.bad_request"
handler403 = "config.views.permission_denied"
handler404 = "config.views.page_not_found"
handler500 = "config.views.server_error"
