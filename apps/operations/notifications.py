"""Email notifications for staff and clients."""

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext as _


def _send(subject, body, recipients):
    if not recipients:
        return
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )


def notify_appointment_request(appointment):
    subject = _("New appointment request from %(name)s") % {"name": appointment.name}
    body = (
        f"Name: {appointment.name}\n"
        f"Email: {appointment.email}\n"
        f"Service: {appointment.service}\n"
        f"Preferred date: {appointment.preferred_date or '—'}\n\n"
        f"Message:\n{appointment.message or '—'}"
    )
    _send(subject, body, [settings.CONTACT_EMAIL])


def notify_client_matter_update(matter, detail):
    client = matter.client
    if not client.email:
        return
    subject = _("Update on your matter %(ref)s") % {"ref": matter.reference_number}
    body = (
        f"Dear {client.full_name},\n\n"
        f"{str(detail)}\n\n"
        f"Matter: {matter.title}\n"
        f"Status: {matter.get_status_display()}\n\n"
        f"— Notaria Notary"
    )
    _send(subject, body, [client.email])
