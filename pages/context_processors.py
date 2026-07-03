from pages.content import load_site_content


def site_content(request):
    language = getattr(request, "LANGUAGE_CODE", None) or "en"
    return load_site_content(language)
