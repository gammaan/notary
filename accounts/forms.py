from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": _("you@example.com"),
            }
        ),
    )
    first_name = forms.CharField(
        label=_("First name"),
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": _("First name")}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": _("Last name")}),
    )
    phone = forms.CharField(
        label=_("Phone"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "placeholder": _("Phone number"),
                "required": False,
            }
        ),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.setdefault("autocomplete", "new-password")
            self.fields[name].widget.attrs.setdefault("placeholder", _("Password"))

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("An account with this email already exists."))
        return email


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": _("you@example.com"),
                "autofocus": True,
                "placeholder": _("you@example.com"),
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": _("Password"),
            }
        ),
    )

    error_messages = {
        "invalid_login": _(
            "Please enter a correct email and password. Note that both fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive."),
    }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "phone": forms.TextInput(
                attrs={
                    "autocomplete": "tel",
                    "placeholder": _("Optional"),
                }
            ),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("autocomplete", "new-password")
