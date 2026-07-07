from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from cms.featured import featured_portfolio, featured_posts
from cms.locale import request_language
from operations.models import AppointmentRequest
from operations.notifications import notify_appointment_request
from pages.content import load_site_content
from pages.forms import ContactForm
from pages.seo import page_seo


def home(request):
    lang = request_language(request)
    site = load_site_content(lang)
    service_options = site.get("company", {}).get("form", {}).get("options", [])

    if request.method == "POST" and request.POST.get("form_type") == "contact":
        contact_form = ContactForm(request.POST, service_choices=service_options or None)
        if contact_form.is_valid():
            data = contact_form.cleaned_data
            appointment = AppointmentRequest.objects.create(
                name=data["name"],
                email=data["email"],
                service=data["service"],
                message=data.get("message", ""),
                preferred_date=data.get("preferred_date"),
            )
            notify_appointment_request(appointment)
            messages.success(
                request,
                _("Thank you — your request was sent. We will contact you shortly."),
            )
            return redirect(request.path + "#contact")
        messages.error(request, _("Please correct the errors below and try again."))
    else:
        contact_form = ContactForm(service_choices=service_options or None)

    ctx = {
        "contact_form": contact_form,
        "featured_posts": featured_posts(lang),
        "featured_portfolio": featured_portfolio(lang),
    }
    ctx.update(
        page_seo(
            request,
            title=_("Notaria Notary | The Art of Certainty"),
            description=_(
                "Notaria Notary — trusted notarial services, a clear process from first contact to sealed documents, and an easy way to book your appointment."
            ),
            path=request.path,
        )
    )
    return render(request, "pages/home.html", ctx)


def privacy(request):
    ctx = page_seo(
        request,
        title=_("Privacy Policy | Notaria Notary"),
        description=_("How Notaria Notary collects, uses, and protects your personal information."),
        path=request.path,
    )
    return render(request, "pages/privacy.html", ctx)


def terms(request):
    ctx = page_seo(
        request,
        title=_("Terms of Service | Notaria Notary"),
        description=_("Terms governing use of the Notaria Notary website and services."),
        path=request.path,
    )
    return render(request, "pages/terms.html", ctx)


def profile_page(request):
    lang = request_language(request)
    site = load_site_content(lang)
    profile = site.get("profile", {})
    ctx = {
        "profile": profile,
    }
    ctx.update(
        page_seo(
            request,
            title=_("{name} | Notary Profile").format(name=profile.get("name", _("Notary"))),
            description=profile.get("summary", _("Meet the notary public behind Notaria Notary.")),
            path=request.path,
        )
    )
    return render(request, "pages/profile.html", ctx)
