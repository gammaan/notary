from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.managers import UserManager

phone_validator = RegexValidator(
    regex=r"^\+?[\d\s\-().]{7,20}$",
    message=_("Enter a valid phone number."),
)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CLIENT = "client", _("Client")
        STAFF = "staff", _("Staff")

    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    phone = models.CharField(
        _("phone"),
        max_length=20,
        blank=True,
        validators=[phone_validator],
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    is_email_verified = models.BooleanField(_("email verified"), default=False)
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def get_full_name(self):
        return self.full_name
