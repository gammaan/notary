# Notaria Notary

Django application for a notary office: public website, staff portal, client records, matters, documents, and finances.

## Quick start (local development)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
cp .env.example .env            # edit if needed; DEBUG=true uses SQLite

python manage.py migrate
python manage.py seed_service_types
python manage.py createsuperuser
python manage.py runserver
```

- Public site: http://127.0.0.1:8000/
- Staff portal: http://127.0.0.1:8000/staff/
- Django admin: http://127.0.0.1:8000/admin/

## Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full checklist.

1. Copy `.env.example` to `.env` and set production values (`DJANGO_DEBUG=false`, PostgreSQL, email, HTTPS URLs).
2. Run migrations and collect static files.
3. Serve with **Gunicorn** behind **nginx** (or use Docker Compose).

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Health check: `GET /health/`

## Docker Compose

```bash
cp .env.example .env
# Set DJANGO_SECRET_KEY, SITE_URL, CSRF_TRUSTED_ORIGINS, DJANGO_ALLOWED_HOSTS

docker compose up --build -d
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_service_types
```

## Project layout

| Path | Purpose |
|------|---------|
| `apps/` | Django applications |
| `config/` | Settings, URLs, WSGI |
| `templates/` | Shared templates |
| `static/` | CSS, JS, themes |
| `data/` | JSON content (company, profile, clients) |
| `locale/` | Translations (en, so, ar) |

Architecture details: [ARCHITECTURE.md](ARCHITECTURE.md)

## Tests

```bash
python manage.py test
python manage.py check --deploy   # security checks (use DJANGO_DEBUG=false)
```
