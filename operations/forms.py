from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import get_user_model

from operations.models import Client, Document, Matter, ServiceType, Transaction
from operations.validators import validate_document_upload
from operations.widgets import StaffFileUploadWidget

STAFF_SELECT2_CLASS = "staff-select2"


def _select_attrs(placeholder):
    return {"data-placeholder": placeholder, "title": placeholder}


def _date_attrs(placeholder):
    return {
        "type": "date",
        "class": "staff-date-input",
        "placeholder": placeholder,
        "title": placeholder,
    }


def _datetime_attrs(placeholder):
    return {
        "type": "datetime-local",
        "class": "staff-datetime-input",
        "placeholder": placeholder,
        "title": placeholder,
    }


def _file_attrs(placeholder):
    return {"title": placeholder, "accept": ".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp"}


def _file_widget(placeholder, layout="inline"):
    if layout == "zone":
        return StaffFileUploadWidget(
            attrs=_file_attrs(placeholder),
            drop_label=_("Drag 'n' drop files here, or click to select files"),
            hint=_("PDF, DOC, DOCX, JPG, PNG or WEBP"),
            layout=layout,
        )
    return StaffFileUploadWidget(
        attrs=_file_attrs(placeholder),
        drop_label=_("Drag and Drop files"),
        hint=_("Click to browse or drop a file here"),
        layout=layout,
    )


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
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": _("Enter your password"),
            }
        ),
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
            "full_name",
            "sex",
            "email",
            "phone",
            "id_number",
            "address",
            "notes",
            "is_active",
        )
        widgets = {
            "full_name": forms.TextInput(
                attrs={"placeholder": _("e.g. Ahmed Hassan"), "autocomplete": "name"}
            ),
            "sex": forms.Select(attrs=_select_attrs(_("Select sex"))),
            "email": forms.EmailInput(attrs={"placeholder": _("you@example.com"), "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": _("+252 61 234 5678"), "autocomplete": "tel"}),
            "id_number": forms.TextInput(attrs={"placeholder": _("Passport or national ID number")}),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": _("Street, district, city")}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": _("Internal notes for staff only")}),
            "is_active": forms.CheckboxInput(attrs={"class": "staff-checkbox-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sex"].choices = [("", _("Select sex"))] + list(Client.Sex.choices)


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
            "status": forms.Select(attrs=_select_attrs(_("Select matter status"))),
            "scheduled_at": forms.DateTimeInput(
                attrs=_datetime_attrs(_("Select date and time"))
            ),
            "assigned_to": forms.Select(attrs={"data-placeholder": _("Assign staff member")}),
            "notes": forms.Textarea(
                attrs={"rows": 3, "placeholder": _("Internal notes for staff only")}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["service_type"].queryset = ServiceType.objects.filter(is_active=True)
        self.fields["client"].queryset = Client.objects.filter(is_active=True).order_by("full_name")
        self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True).order_by(
            "first_name", "last_name"
        )
        if not self.is_bound and not self.initial.get("scheduled_at"):
            if not getattr(self.instance, "pk", None):
                self.fields["scheduled_at"].initial = _default_scheduled_datetime()


class MatterWizardClientForm(forms.Form):
    client = forms.ModelChoiceField(
        label=_("Client"),
        queryset=Client.objects.filter(is_active=True).order_by("full_name"),
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
            attrs=_datetime_attrs(_("Select date and time"))
        ),
    )
    status = forms.ChoiceField(
        label=_("Status"),
        choices=Matter.Status.choices,
        initial=Matter.Status.INQUIRY,
        widget=forms.Select(attrs=_select_attrs(_("Select matter status"))),
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
    file = forms.FileField(
        label=_("File"),
        required=False,
        widget=_file_widget(_("Choose PDF, DOC, or image file"), layout="zone"),
    )
    status = forms.ChoiceField(
        label=_("Status"),
        choices=Document.Status.choices,
        initial=Document.Status.RECEIVED,
        required=False,
        widget=forms.Select(attrs=_select_attrs(_("Select document status"))),
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
        choices=[("", _("Select payment method"))] + list(Transaction.PaymentMethod.choices),
        required=False,
        widget=forms.Select(attrs=_select_attrs(_("Select payment method"))),
    )
    status = forms.ChoiceField(
        label=_("Payment status"),
        choices=Transaction.Status.choices,
        initial=Transaction.Status.PENDING,
        required=False,
        widget=forms.Select(attrs=_select_attrs(_("Select payment status"))),
    )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("title", "document_type", "file", "status", "notes")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": _("e.g. Sale agreement")}),
            "document_type": forms.TextInput(attrs={"placeholder": _("e.g. Contract, ID copy")}),
            "file": _file_widget(_("Drag and Drop files"), layout="zone"),
            "status": forms.Select(attrs=_select_attrs(_("Select document status"))),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": _("Optional notes about this document")}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            validate_document_upload(file)
        elif not self.instance.pk:
            raise forms.ValidationError(_("Please upload a file."))
        return file


class MatterTransactionForm(forms.ModelForm):
    """Matter-scoped entry — type is set by the view (income vs expense tab)."""

    class Meta:
        model = Transaction
        fields = (
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
            "currency": forms.TextInput(attrs={"placeholder": _("e.g. USD")}),
            "payment_method": forms.Select(attrs=_select_attrs(_("Select payment method"))),
            "status": forms.Select(attrs=_select_attrs(_("Select payment status"))),
            "transaction_date": forms.DateInput(attrs=_date_attrs(_("Select transaction date"))),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": _("Optional payment notes")}),
        }

    def __init__(self, *args, **kwargs):
        self.entry_type = kwargs.pop("entry_type", Transaction.Type.INCOME)
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.initial.get("transaction_date"):
            self.fields["transaction_date"].initial = _default_today_date()
        payment_choices = [("", _("Select payment method"))] + list(
            Transaction.PaymentMethod.choices
        )
        self.fields["payment_method"].choices = payment_choices
        if self.entry_type == Transaction.Type.EXPENSE:
            self.fields["description"].widget.attrs["placeholder"] = _("e.g. Filing fee, travel cost")
        if self.instance.pk:
            from operations.transaction_rules import transaction_is_locked

            ref_matter = getattr(self.instance, "matter", None)
            if ref_matter and transaction_is_locked(self.instance, ref_matter):
                for field in self.fields.values():
                    field.disabled = True


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
            "transaction_type": forms.Select(attrs=_select_attrs(_("Income or expense"))),
            "description": forms.TextInput(attrs={"placeholder": _("e.g. Service fee")}),
            "amount": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01"}),
            "currency": forms.TextInput(attrs={"placeholder": _("e.g. USD")}),
            "payment_method": forms.Select(attrs=_select_attrs(_("Select payment method"))),
            "status": forms.Select(attrs=_select_attrs(_("Select payment status"))),
            "transaction_date": forms.DateInput(attrs=_date_attrs(_("Select transaction date"))),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": _("Optional payment notes")}),
        }

    def __init__(self, *args, **kwargs):
        matter = kwargs.pop("matter", None)
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.initial.get("transaction_date"):
            self.fields["transaction_date"].initial = _default_today_date()
        payment_choices = [("", _("Select payment method"))] + list(
            Transaction.PaymentMethod.choices
        )
        self.fields["payment_method"].choices = payment_choices
        if self.instance.pk:
            from operations.transaction_rules import transaction_is_locked

            ref_matter = matter or getattr(self.instance, "matter", None)
            if ref_matter and transaction_is_locked(self.instance, ref_matter):
                for field in self.fields.values():
                    field.disabled = True


class GeneralTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            "category",
            "description",
            "amount",
            "currency",
            "payment_method",
            "status",
            "transaction_date",
            "notes",
        )
        widgets = {
            "category": forms.Select(attrs=_select_attrs(_("Select category"))),
            "description": forms.TextInput(
                attrs={"placeholder": _("e.g. Office rent — March")}
            ),
            "amount": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01"}),
            "currency": forms.TextInput(attrs={"placeholder": _("e.g. USD")}),
            "payment_method": forms.Select(attrs=_select_attrs(_("Select payment method"))),
            "status": forms.Select(attrs=_select_attrs(_("Select payment status"))),
            "transaction_date": forms.DateInput(attrs=_date_attrs(_("Select transaction date"))),
            "notes": forms.Textarea(
                attrs={"rows": 3, "placeholder": _("Optional notes")}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.entry_type = kwargs.pop("entry_type", Transaction.Type.EXPENSE)
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.initial.get("transaction_date"):
            self.fields["transaction_date"].initial = _default_today_date()
        if not self.is_bound and not self.initial.get("currency"):
            self.fields["currency"].initial = "USD"
        payment_choices = [("", _("Select payment method"))] + list(
            Transaction.PaymentMethod.choices
        )
        self.fields["payment_method"].choices = payment_choices
        txn_type = self.entry_type
        if self.is_bound:
            txn_type = self.entry_type
        self._set_category_choices(txn_type)
        if txn_type == Transaction.Type.INCOME:
            self.fields["description"].widget.attrs["placeholder"] = _("e.g. Consulting fee, referral")
        else:
            self.fields["description"].widget.attrs["placeholder"] = _("e.g. Office rent — March")

    def _set_category_choices(self, txn_type):
        if txn_type == Transaction.Type.INCOME:
            cats = Transaction.INCOME_CATEGORIES
        else:
            cats = Transaction.EXPENSE_CATEGORIES
        self.fields["category"].choices = [("", _("Select category"))] + [
            (c.value, c.label) for c in cats
        ]

    def clean(self):
        cleaned = super().clean()
        txn_type = self.entry_type
        category = cleaned.get("category")
        if txn_type == Transaction.Type.EXPENSE:
            allowed = {c.value for c in Transaction.EXPENSE_CATEGORIES}
        else:
            allowed = {c.value for c in Transaction.INCOME_CATEGORIES}
        if category and category not in allowed:
            self.add_error("category", _("Choose a category for this transaction type."))
        return cleaned
