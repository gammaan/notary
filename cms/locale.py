"""Language helpers for CMS public content."""

SUPPORTED_LANGUAGES = frozenset({"en", "so", "ar"})


def normalize_language(code):
    lang = (code or "en").split("-")[0].lower()
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def request_language(request):
    return normalize_language(getattr(request, "LANGUAGE_CODE", "en"))


def filter_by_language(queryset, language, *, fallback=True):
    localized = queryset.filter(language=language)
    if fallback and language != "en" and not localized.exists():
        return queryset.filter(language="en")
    return localized
