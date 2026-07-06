from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(
        label=_("Full name"),
        max_length=120,
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": _("Your full name")}),
    )
    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": _("you@example.com")}),
    )
    service = forms.CharField(
        label=_("Service needed"),
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": _("Which service do you need?")}),
    )
    message = forms.CharField(
        label=_("Message"),
        required=False,
        max_length=2000,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": _("Tell us about your request (optional)")}
        ),
    )
    preferred_date = forms.DateField(
        label=_("Preferred date"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "staff-date-input"}),
    )

    def __init__(self, *args, service_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if service_choices:
            self.fields["service"] = forms.ChoiceField(
                label=_("Service needed"),
                choices=[(s, s) for s in service_choices],
                widget=forms.Select(),
            )
