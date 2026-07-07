import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_AVATAR_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})
AVATAR_MAX_BYTES = 2 * 1024 * 1024


def validate_avatar_upload(file):
    if not file:
        return

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValidationError(
            _("Unsupported image type. Use JPG, PNG, WebP, or GIF."),
        )

    if file.size > AVATAR_MAX_BYTES:
        raise ValidationError(_("Photo is too large. Maximum size is 2 MB."))
