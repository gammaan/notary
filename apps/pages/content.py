from pathlib import Path
import json

from django.conf import settings

DATA_DIR = Path(settings.BASE_DIR) / "data"


def _load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def _deep_merge(base, override):
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = _deep_merge(merged.get(key), value)
        return merged

    if isinstance(base, list) and isinstance(override, list):
        return [
            _deep_merge(base_item, override_item)
            for base_item, override_item in zip(base, override)
        ]

    return override if override is not None else base


def _localized_json(filename: str, language_code: str) -> dict:
    data = _load_json(filename)
    translations = data.pop("translations", {})
    language = (language_code or "en").split("-")[0]
    return _deep_merge(data, translations.get(language, {}))


def _active_social(social: dict) -> list[dict]:
    icons = {
        "facebook": "Facebook",
        "instagram": "Instagram",
        "linkedin": "LinkedIn",
        "x": "X",
        "whatsapp": "WhatsApp",
    }
    return [
        {"id": platform, "url": url, "label": icons.get(platform, platform.title())}
        for platform, url in social.items()
        if url
    ]


def load_site_content(language_code: str = "en") -> dict:
    company = _localized_json("company.json", language_code)
    return {
        "company": company,
        "social_links": _active_social(company.get("social", {})),
        "services": _localized_json("services.json", language_code)["items"],
        "workflow": _localized_json("workflow.json", language_code)["items"],
        "security_features": _localized_json("security.json", language_code)["items"],
        "marquee": _localized_json("marquee.json", language_code)["items"],
        "profile": _localized_json("profile.json", language_code),
        "clients_marquee": _localized_json("clients_marquee.json", language_code),
    }

