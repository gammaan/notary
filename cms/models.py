from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class ContentLanguage(models.TextChoices):
    EN = "en", _("English")
    SO = "so", _("Somali")
    AR = "ar", _("Arabic")


class Post(models.Model):
    class Category(models.TextChoices):
        BLOG = "blog", _("Blog")
        NEWS = "news", _("News")
        NOTICE = "notice", _("Notice")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    language = models.CharField(
        max_length=5,
        choices=ContentLanguage.choices,
        default=ContentLanguage.EN,
        db_index=True,
    )
    summary = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.BLOG,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = _("post")
        verbose_name_plural = _("posts")
        constraints = [
            models.UniqueConstraint(fields=["language", "slug"], name="cms_post_language_slug"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "post"
            slug = base
            counter = 1
            while (
                Post.objects.filter(language=self.language, slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED


class PortfolioItem(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    language = models.CharField(
        max_length=5,
        choices=ContentLanguage.choices,
        default=ContentLanguage.EN,
        db_index=True,
    )
    document_type = models.CharField(
        max_length=120,
        blank=True,
        help_text=_("e.g. Real estate, Affidavit, Business contract"),
    )
    summary = models.TextField()
    body = models.TextField(
        blank=True,
        help_text=_("Optional longer description. Keep client details anonymous."),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-published_at", "-created_at"]
        verbose_name = _("portfolio item")
        verbose_name_plural = _("portfolio items")
        constraints = [
            models.UniqueConstraint(
                fields=["language", "slug"],
                name="cms_portfolio_language_slug",
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "portfolio-item"
            slug = base
            counter = 1
            while (
                PortfolioItem.objects.filter(language=self.language, slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED
