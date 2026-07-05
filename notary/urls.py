from django.conf import settings

from django.conf.urls.i18n import i18n_patterns

from django.contrib import admin

from django.urls import include, path

from django.conf.urls.static import static

from cms.views import blog_detail, blog_list, portfolio_detail, portfolio_list
from pages.views import home



urlpatterns = [

    path("i18n/", include("django.conf.urls.i18n")),

    path("staff/", include("operations.urls")),

]



urlpatterns += i18n_patterns(

    path("", home, name="home"),

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

