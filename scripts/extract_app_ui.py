"""Extract admin layout CSS to app-ui.css with .app-* aliases; keep Bootstrap overrides in admin.css."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "/* ── Bootstrap coexistence"


def expand_selector_list(selectors: str) -> str:
    parts = [part.strip() for part in selectors.split(",") if part.strip()]
    expanded: list[str] = []
    for part in parts:
        if part not in expanded:
            expanded.append(part)
        if ".staff-" in part:
            alias = re.sub(r"\.staff-", ".app-", part)
            if alias not in expanded:
                expanded.append(alias)
    return ", ".join(expanded)


def alias_staff_selectors(css: str) -> str:
    out: list[str] = []
    for line in css.splitlines():
        if "{" in line and ".staff-" in line.split("{", 1)[0]:
            selector, rest = line.split("{", 1)
            line = expand_selector_list(selector) + "{" + rest
        out.append(line)
    return "\n".join(out) + "\n"


def alias_body_scoped(css: str) -> str:
    return re.sub(r"\.staff-body\b", ".app-body, .staff-body", css)


def main() -> None:
    admin_path = ROOT / "static/apps/admin/admin.css"
    admin_css = admin_path.read_text(encoding="utf-8")
    if MARKER not in admin_css:
        raise ValueError("Bootstrap coexistence marker not found")

    core_css, bootstrap_css = admin_css.split(MARKER, 1)
    app_ui = (
        "/**\n"
        " * Reusable application UI (admin portal and authenticated layouts).\n"
        " * Each rule targets .app-* and .staff-* so either naming works.\n"
        " */\n\n"
        + alias_staff_selectors(core_css.strip())
        + "\n"
    )
    (ROOT / "static/core/css/app-ui.css").write_text(app_ui, encoding="utf-8")

    admin_out = (
        "/**\n"
        " * Staff portal: Bootstrap coexistence and portal-specific overrides.\n"
        " * Core UI components: static/core/css/app-ui.css\n"
        " */\n\n"
        + MARKER
        + alias_body_scoped(bootstrap_css)
    )
    admin_path.write_text(admin_out, encoding="utf-8")
    print("Created app-ui.css and trimmed admin.css")


if __name__ == "__main__":
    main()
