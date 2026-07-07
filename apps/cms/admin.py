from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from cms.models import ContentLanguage, PortfolioItem, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "category", "status", "is_featured", "published_at", "updated_at")
    list_filter = ("language", "category", "status", "is_featured")
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "language", "category", "status", "is_featured")}),
        (_("Content"), {"fields": ("summary", "body")}),
        (_("Publishing"), {"fields": ("published_at",)}),
    )


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "document_type", "status", "is_featured", "sort_order", "published_at")
    list_filter = ("language", "status", "is_featured", "document_type")
    search_fields = ("title", "summary", "body", "document_type")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("sort_order", "-published_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "language", "document_type", "status", "is_featured", "sort_order")}),
        (_("Content"), {"fields": ("summary", "body")}),
        (_("Publishing"), {"fields": ("published_at",)}),
    )
