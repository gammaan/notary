from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from operations.models import Client, Document, Matter, ServiceType, Transaction


class MatterInline(admin.TabularInline):
    model = Matter
    extra = 0
    fields = ("reference_number", "title", "service_type", "status", "scheduled_at")
    readonly_fields = ("reference_number",)
    show_change_link = True


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ("title", "document_type", "status", "file")
    show_change_link = True


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fields = (
        "transaction_type",
        "description",
        "amount",
        "status",
        "payment_method",
        "transaction_date",
    )
    show_change_link = True


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("first_name", "last_name", "email", "phone", "id_number")
    readonly_fields = ("created_at", "updated_at")
    inlines = (MatterInline,)
    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "is_active")}),
        (_("Contact"), {"fields": ("email", "phone", "address")}),
        (_("Identification"), {"fields": ("id_number",)}),
        (_("Notes"), {"fields": ("notes",)}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Name"))
    def full_name(self, obj):
        return obj.full_name


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "default_fee", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("sort_order", "name")


@admin.register(Matter)
class MatterAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "title",
        "client",
        "service_type",
        "status",
        "scheduled_at",
        "assigned_to",
    )
    list_filter = ("status", "service_type", "assigned_to", "created_at")
    search_fields = (
        "reference_number",
        "title",
        "description",
        "client__first_name",
        "client__last_name",
        "client__email",
    )
    readonly_fields = ("reference_number", "created_at", "updated_at", "completed_at")
    autocomplete_fields = ("client", "service_type", "assigned_to")
    date_hierarchy = "scheduled_at"
    inlines = (DocumentInline, TransactionInline)
    fieldsets = (
        (None, {"fields": ("reference_number", "title", "client", "service_type", "status")}),
        (_("Schedule"), {"fields": ("scheduled_at", "completed_at", "assigned_to")}),
        (_("Details"), {"fields": ("description", "notes")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "matter", "document_type", "status", "uploaded_by", "created_at")
    list_filter = ("status", "document_type", "created_at")
    search_fields = ("title", "document_type", "matter__reference_number", "matter__title")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("matter", "uploaded_by")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "matter",
        "transaction_type",
        "description",
        "amount",
        "currency",
        "status",
        "transaction_date",
    )
    list_filter = ("transaction_type", "status", "payment_method", "transaction_date")
    search_fields = ("description", "matter__reference_number", "notes")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("matter", "recorded_by")
    date_hierarchy = "transaction_date"
