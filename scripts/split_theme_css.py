"""Split theme CSS: structural -> base.css, colors-only -> theme-*.css."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def split_theme(text: str) -> tuple[str, str, str]:
    marker = "\n*,"
    start = text.find(marker)
    if start == -1:
        raise ValueError("Could not find structural CSS marker")
    head = text[:start]
    structural = text[start + 1 :]
    root_end = head.find('[data-theme="dark"]')
    if root_end == -1:
        raise ValueError("Could not find dark theme block")
    root = head[:root_end].strip()
    colors = head[root_end:].strip()
    return root, colors, structural


def main() -> None:
    theme_dir = ROOT / "static/themes"
    theme1 = (theme_dir / "theme-1.css").read_text(encoding="utf-8")
    theme2 = (theme_dir / "theme-2.css").read_text(encoding="utf-8")
    theme3 = (theme_dir / "theme-3.css").read_text(encoding="utf-8")

    root, colors1, structural = split_theme(theme1)
    _, colors2, _ = split_theme(theme2)
    _, colors3, _ = split_theme(theme3)

    base_header = (
        "/**\n"
        " * Shared design system: layout, typography, components.\n"
        " * Color tokens: static/themes/theme-*.css\n"
        " * Admin UI: static/core/css/app-ui.css\n"
        " */\n\n"
    )
    (ROOT / "static/core/css/base.css").write_text(
        base_header + root + "\n\n" + structural,
        encoding="utf-8",
    )

    def theme_file(label: str, colors: str) -> str:
        return (
            f"/**\n * {label} — color tokens only.\n"
            f" * Layout/components: static/core/css/base.css\n */\n\n{colors}\n"
        )

    (theme_dir / "theme-1.css").write_text(theme_file("Theme 1 (blue)", colors1), encoding="utf-8")
    (theme_dir / "theme-2.css").write_text(theme_file("Theme 2 (green)", colors2), encoding="utf-8")
    (theme_dir / "theme-3.css").write_text(theme_file("Theme 3 (violet)", colors3), encoding="utf-8")

    print("Done splitting themes into base.css + color-only theme files.")


if __name__ == "__main__":
    main()
