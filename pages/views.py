from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from cms.featured import featured_portfolio, featured_posts
from cms.locale import request_language
from pages.content import load_site_content
from pages.forms import ContactForm
from pages.seo import page_seo


def home(request):
    lang = request_language(request)
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

    ctx = {
        "contact_form": contact_form,
        "featured_posts": featured_posts(lang),
        "featured_portfolio": featured_portfolio(lang),
    }
    ctx.update(
        page_seo(
            request,
            title=_("Himilo Notary | The Art of Certainty"),
            description=_(
                "Himilo Notary — trusted notarial services, a clear process from first contact to sealed documents, and an easy way to book your appointment."
            ),
            path=request.path,
        )
    )
    return render(request, "pages/home.html", ctx)


def privacy(request):
    ctx = page_seo(
        request,
        title=_("Privacy Policy | Himilo Notary"),
        description=_("How Himilo Notary collects, uses, and protects your personal information."),
        path=request.path,
    )
    return render(request, "pages/privacy.html", ctx)


def terms(request):
    ctx = page_seo(
        request,
        title=_("Terms of Service | Himilo Notary"),
        description=_("Terms governing use of the Himilo Notary website and services."),
        path=request.path,
    )
    return render(request, "pages/terms.html", ctx)
