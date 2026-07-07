# Project layout

Reusable structure for Notaria Notary and future client deployments.

## Directory map

```
notary/                    # Repository root
├── config/                # Django project settings
├── apps/                  # Django applications
├── static/
│   ├── core/              # Shared, theme-agnostic assets
│   │   ├── css/
│   │   │   ├── base.css       # Layout, typography, public components
│   │   │   ├── grid.css       # 12-column grid
│   │   │   ├── app-ui.css     # Reusable admin/app shell (.app-* + .staff-*)
│   │   │   └── public-pages.css
│   │   └── js/site.js
│   ├── themes/            # Color tokens only (one file per palette)
│   │   ├── theme-1.css    # Blue (default)
│   │   ├── theme-2.css    # Teal
│   │   └── theme-3.css    # Indigo
│   └── apps/admin/        # Admin portal JS + Bootstrap overrides
│       ├── admin.css      # Bootstrap coexistence only
│       └── admin.js, …
├── templates/core/        # base_public.html, base_admin.html
├── data/                  # Per-deployment JSON content
└── locale/
```

## CSS load order

**Public** (`core/base_public.html`):

1. `core/css/base.css` — structure & components  
2. `core/css/grid.css`  
3. `themes/{SITE_THEME}.css` — colors only  
4. `core/css/public-pages.css` — page-specific blocks  

**Admin** (`core/base_admin.html`):

1. `core/css/base.css`  
2. `core/css/grid.css`  
3. `core/css/app-ui.css` — shell, sidebar, tables, forms (`.app-*` / `.staff-*`)  
4. `themes/{SITE_THEME}.css` — colors  
5. Bootstrap 5.3  
6. `apps/admin/admin.css` — Bootstrap overrides  

## Theme selection

```bash
SITE_THEME=theme-1   # blue (default)
SITE_THEME=theme-2   # teal
SITE_THEME=theme-3   # indigo
```

Each theme file defines `[data-theme="dark"]` and `[data-theme="light"]` CSS variables only. Layout lives in `base.css`.

## Reusable class names

Admin templates may use either prefix:

| Generic | Legacy alias |
|---------|----------------|
| `.app-shell` | `.staff-shell` |
| `.app-sidebar` | `.staff-sidebar` |
| `.app-panel` | `.staff-panel` |
| `.app-table` | `.staff-table` |
| `.app-link` | `.staff-link` |

New authenticated layouts should prefer `.app-*`.

## Running locally

```bash
python manage.py runserver
```

Settings module: `config.settings`.
