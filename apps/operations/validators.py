import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_DOCUMENT_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".txt",
    }
)


def validate_document_upload(file):
    if not file:
        return

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            _("Unsupported file type “%(ext)s”. Allowed: PDF, Word, images, or TXT."),
            params={"ext": ext or "?"},
        )

    max_bytes = 10 * 1024 * 1024  # 10 MB; override via settings in form
    from django.conf import settings

    max_bytes = getattr(settings, "DOCUMENT_MAX_UPLOAD_SIZE", max_bytes)
    if file.size > max_bytes:
        raise ValidationError(
            _("File is too large. Maximum size is %(mb)s MB."),
            params={"mb": max_bytes // (1024 * 1024)},
        )
