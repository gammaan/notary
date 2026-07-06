from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from pages.content import load_site_content
from pages.forms import ContactForm


def home(request):
    lang = getattr(request, "LANGUAGE_CODE", "en") or "en"
    site = load_site_content(lang)
    service_options = site.get("notary", {}).get("form", {}).get("options", [])

    if request.method == "POST" and request.POST.get("form_type") == "contact":
        contact_form = ContactForm(request.POST, service_choices=service_options or None)
        if contact_form.is_valid():
            data = contact_form.cleaned_data
            subject = _("New appointment request from %(name)s") % {"name": data["name"]}
            body = (
                f"Name: {data['name']}\n"
                f"Email: {data['email']}\n"
                f"Service: {data['service']}\n\n"
                f"Message:\n{data.get('message') or '—'}"
            )
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(
                request,
                _("Thank you — your request was sent. We will contact you shortly."),
            )
            return redirect(request.path + "#contact")
        messages.error(request, _("Please correct the errors below and try again."))
    else:
        contact_form = ContactForm(service_choices=service_options or None)

    return render(request, "pages/home.html", {"contact_form": contact_form})
