# Site themes

Each file defines color tokens and public-site styling for one deployment.

| File | Palette |
|------|---------|
| `theme-1.css` | Blue (default — Notaria Notary) |
| `theme-2.css` | Teal |
| `theme-3.css` | Indigo |

Set the active theme in environment or settings:

```
SITE_THEME=theme-1
```

Admin UI styles live in `static/apps/admin/admin.css` and load on top of the active theme.
