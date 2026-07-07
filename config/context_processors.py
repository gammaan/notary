from django.conf import settings


def site_theme(request):
    theme = getattr(settings, "SITE_THEME", "theme-1")
    return {
        "site_theme": theme,
        "theme_css_path": f"themes/{theme}.css",
    }
