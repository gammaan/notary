from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from operations.models import Client, Document, Matter, ServiceType, Transaction

STAFF_SELECT2_CLASS = "staff-select2"


def _default_scheduled_datetime():
    return timezone.localtime(timezone.now()).replace(second=0, microsecond=0)


def _default_today_date():
    return timezone.localdate()


class StaffLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": _("you@example.com"),
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": _("Please enter a correct email and password."),
        "inactive": _("This account is inactive."),
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(
                _("This login is for staff only. Contact your administrator."),
                code="not_staff",
            )


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "id_number",
            "address",
            "notes",
            "is_active",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": _("e.g. Ahmed"), "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"placeholder": _("e.g. Hassan"), "autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"placeholder": _("you@example.com"), "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": _("+252 61 234 5678"), "autocomplete": "tel"}),
            "id_number": forms.TextInput(attrs={"placeholder": _("Passport or national ID number")}),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": _("Street, district, city")}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": _("Internal notes for staff only")}),
            "is_active": forms.CheckboxInput(attrs={"class": "staff-checkbox-input"}),
        }


class MatterForm(forms.ModelForm):
    class Meta:
        model = Matter
        fields = (
            "client",
            "service_type",
            "title",
            "description",
            "status",
            "scheduled_at",
            "assigned_to",
            "notes",
        )
        widgets = {
            "client": forms.Select(
                attrs={
                    "class": STAFF_SELECT2_CLASS,
                    "data-placeholder": _("Search for a client…"),
                    "data-allow-clear": "true",
                }
            ),
            "service_type": forms.Select(attrs={"data-placeholder": _("Select a service")}),
            "title": forms.TextInput(attrs={"placeholder": _("e.g. Property sale notarization")}),
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": _("Brief description of the matter")}
            ),
            "status": forms.Select(),
            "scheduled_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "staff-datetime-input"}
            ),
            "assigned_to": forms.Select(attrs={"data-placeholder": _("Assign staff member")}),
            "notes": forms.Textarea(
                attrs={"rows": 3, "placeholder": _("Internal notes for staff only")}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service_type"].queryset = ServiceType.objects.filter(is_active=True)
        self.fields["client"].queryset = Client.objects.filter(is_active=True).order_by(
            "last_name", "first_name"
        )
        if not self.is_bound and not self.initial.get("scheduled_at"):
            if not getattr(self.instance, "pk", None):
                self.fields["scheduled_at"].initial = _default_scheduled_datetime()


class MatterWizardClientForm(forms.Form):
    client = forms.ModelChoiceField(
        label=_("Client"),
        queryset=Client.objects.filter(is_active=True).order_by("last_name", "first_name"),
        empty_label=_("Select a client"),
        widget=forms.Select(
            attrs={
                "class": STAFF_SELECT2_CLASS,
                "data-placeholder": _("Search for a client…"),
            }
        ),
    )


class MatterWizardDetailsForm(forms.Form):
    service_type = forms.ModelChoiceField(
        label=_("Service type"),
        queryset=ServiceType.objects.filter(is_active=True),
        widget=forms.Select(attrs={"data-placeholder": _("Select a service")}),
    )
    title = forms.CharField(
        label=_("Matter title"),
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": _("e.g. Property sale notarization")}),
    )
    description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 4, "placeholder": _("Brief description of the matter")}
        ),
    )
    scheduled_at = forms.DateTimeField(
        label=_("Scheduled for"),
        required=False,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "staff-datetime-input"}
        ),
    )
    status = forms.ChoiceField(
        label=_("Status"),
        choices=Matter.Status.choices,
        initial=Matter.Status.INQUIRY,
        widget=forms.Select(),
    )
    create_fee = forms.BooleanField(
        label=_("Create pending fee from service default"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "staff-checkbox-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.initial.get("scheduled_at"):
            self.fields["scheduled_at"].initial = _default_scheduled_datetime()


class MatterWizardDocumentForm(forms.Form):
    skip = forms.BooleanField(
        label=_("Skip for now"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "staff-checkbox-input"}),
    )
    title = forms.CharField(
        label=_("Document title"),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("e.g. Sale agreement")}),
    )
    document_type = forms.CharField(
        label=_("Document type"),
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("e.g. Contract, ID copy")}),
    )
    file = forms.FileField(label=_("File"), required=False)
    status = forms.ChoiceField(
        label=_("Status"),
        choices=Document.Status.choices,
        initial=Document.Status.RECEIVED,
        required=False,
    )


class MatterWizardPaymentForm(forms.Form):
    skip = forms.BooleanField(
        label=_("Skip for now"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "staff-checkbox-input"}),
    )
    description = forms.CharField(
        label=_("Description"),
        max_length=255,
        initial=_("Service fee"),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("e.g. Service fee")}),
    )
    amount = forms.DecimalField(
        label=_("Amount"),
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01"}),
    )
    payment_method = forms.ChoiceField(
        label=_("Payment method"),
        choices=[("", _("— Select —"))] + list(Transaction.PaymentMethod.choices),
        required=False,
    )
    status = forms.ChoiceField(
        label=_("Payment status"),
        choices=Transaction.Status.choices,
        initial=Transaction.Status.PENDING,
        required=False,
    )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("title", "document_type", "file", "status", "notes")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": _("e.g. Sale agreement")}),
            "document_type": forms.TextInput(attrs={"placeholder": _("e.g. Contract, ID copy")}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": _("Optional notes about this document")}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            "transaction_type",
            "description",
            "amount",
            "currency",
            "payment_method",
            "status",
            "transaction_date",
            "notes",
        )
        widgets = {
            "description": forms.TextInput(attrs={"placeholder": _("e.g. Service fee")}),
            "amount": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01"}),
            "currency": forms.TextInput(attrs={"placeholder": "USD"}),
            "transaction_date": forms.DateInput(attrs={"type": "date", "class": "staff-date-input"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": _("Optional payment notes")}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.initial.get("transaction_date"):
            self.fields["transaction_date"].initial = _default_today_date()
