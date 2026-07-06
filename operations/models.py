from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

phone_validator = RegexValidator(
    regex=r"^\+?[\d\s\-().]{7,20}$",
    message=_("Enter a valid phone number."),
)


class Client(models.Model):
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    email = models.EmailField(_("email"), blank=True)
    phone = models.CharField(
        _("phone"),
        max_length=20,
        blank=True,
        validators=[phone_validator],
    )
    id_number = models.CharField(
        _("ID / passport number"),
        max_length=64,
        blank=True,
        help_text=_("Government ID or passport reference, if provided."),
    )
    address = models.TextField(_("address"), blank=True)
    notes = models.TextField(_("internal notes"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_profile",
        verbose_name=_("portal user"),
    )
    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = _("client")
        verbose_name_plural = _("clients")

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class ServiceType(models.Model):
    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    default_fee = models.DecimalField(
        _("default fee"),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(_("active"), default=True)
    sort_order = models.PositiveIntegerField(_("sort order"), default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("service type")
        verbose_name_plural = _("service types")

    def __str__(self):
        return self.name


class Matter(models.Model):
    class Status(models.TextChoices):
        INQUIRY = "inquiry", _("Inquiry")
        SCHEDULED = "scheduled", _("Scheduled")
        IN_PROGRESS = "in_progress", _("In progress")
        AWAITING_PAYMENT = "awaiting_payment", _("Awaiting payment")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    reference_number = models.CharField(
        _("reference"),
        max_length=32,
        unique=True,
        blank=True,
        editable=False,
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="matters",
        verbose_name=_("client"),
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="matters",
        verbose_name=_("service type"),
    )
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.INQUIRY,
    )
    scheduled_at = models.DateTimeField(_("scheduled for"), null=True, blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_matters",
        verbose_name=_("assigned to"),
    )
    notes = models.TextField(_("internal notes"), blank=True)
    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("matter")
        verbose_name_plural = _("matters")

    def __str__(self):
        return f"{self.reference_number} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def _generate_reference_number(self):
        year = timezone.now().year
        prefix = f"MAT-{year}-"
        last = (
            Matter.objects.filter(reference_number__startswith=prefix)
            .exclude(pk=self.pk)
            .order_by("-reference_number")
            .values_list("reference_number", flat=True)
            .first()
        )
        if last:
            try:
                sequence = int(last.rsplit("-", 1)[-1]) + 1
            except ValueError:
                sequence = 1
        else:
            sequence = 1
        return f"{prefix}{sequence:04d}"


def document_upload_path(instance, filename):
    matter_ref = instance.matter.reference_number if instance.matter_id else "unassigned"
    return f"documents/{matter_ref}/{filename}"


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        RECEIVED = "received", _("Received")
        VERIFIED = "verified", _("Verified")
        NOTARIZED = "notarized", _("Notarized")
        ARCHIVED = "archived", _("Archived")

    matter = models.ForeignKey(
        Matter,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("matter"),
    )
    title = models.CharField(_("title"), max_length=200)
    document_type = models.CharField(_("document type"), max_length=120, blank=True)
    file = models.FileField(_("file"), upload_to=document_upload_path, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    notes = models.TextField(_("notes"), blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
        verbose_name=_("uploaded by"),
    )
    created_at = models.DateTimeField(_("uploaded"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("document")
        verbose_name_plural = _("documents")

    def __str__(self):
        return self.title


class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "income", _("Income")
        EXPENSE = "expense", _("Expense")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PARTIAL = "partial", _("Partially paid")
        PAID = "paid", _("Paid")
        WAIVED = "waived", _("Waived")
        CANCELLED = "cancelled", _("Cancelled")

    class PaymentMethod(models.TextChoices):
        CASH = "cash", _("Cash")
        BANK = "bank", _("Bank transfer")
        MOBILE = "mobile", _("Mobile money")
        CARD = "card", _("Card")
        OTHER = "other", _("Other")

    matter = models.ForeignKey(
        Matter,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("matter"),
    )
    transaction_type = models.CharField(
        _("type"),
        max_length=20,
        choices=Type.choices,
        default=Type.INCOME,
    )
    description = models.CharField(_("description"), max_length=255)
    amount = models.DecimalField(
        _("amount"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(_("currency"), max_length=8, default="USD")
    payment_method = models.CharField(
        _("payment method"),
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    transaction_date = models.DateField(_("transaction date"), default=timezone.now)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_transactions",
        verbose_name=_("recorded by"),
    )
    notes = models.TextField(_("notes"), blank=True)
    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount} — {self.matter.reference_number}"

    @property
    def is_locked(self):
        return self.status in (
            self.Status.PAID,
            self.Status.WAIVED,
            self.Status.CANCELLED,
        )


class AuditLog(models.Model):
    class EntityType(models.TextChoices):
        MATTER = "matter", _("Matter")
        DOCUMENT = "document", _("Document")
        TRANSACTION = "transaction", _("Transaction")
        CLIENT = "client", _("Client")

    class Action(models.TextChoices):
        CREATED = "created", _("Created")
        UPDATED = "updated", _("Updated")
        DELETED = "deleted", _("Deleted")
        STATUS_CHANGED = "status_changed", _("Status changed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("user"),
    )
    action = models.CharField(_("action"), max_length=20, choices=Action.choices)
    entity_type = models.CharField(_("entity type"), max_length=20, choices=EntityType.choices)
    entity_id = models.PositiveIntegerField(_("entity id"))
    entity_label = models.CharField(_("entity"), max_length=255)
    detail = models.CharField(_("detail"), max_length=500, blank=True)
    matter = models.ForeignKey(
        Matter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("matter"),
    )
    created_at = models.DateTimeField(_("logged at"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("audit log entry")
        verbose_name_plural = _("audit log")

    def __str__(self):
        return f"{self.get_action_display()} {self.entity_label}"


class AppointmentRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        CANCELLED = "cancelled", _("Cancelled")

    name = models.CharField(_("full name"), max_length=120)
    email = models.EmailField(_("email"))
    service = models.CharField(_("service needed"), max_length=200)
    message = models.TextField(_("message"), blank=True)
    preferred_date = models.DateField(_("preferred date"), null=True, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(_("submitted"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("appointment request")
        verbose_name_plural = _("appointment requests")

    def __str__(self):
        return f"{self.name} — {self.service}"
