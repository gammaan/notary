"""PDF generation for staff documents."""

from io import BytesIO

from django.http import HttpResponse
from django.template.loader import render_to_string


def render_pdf_response(template_name, context, filename="document.pdf"):
    html = render_to_string(template_name, context)
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return None

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
