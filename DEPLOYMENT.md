# Production deployment guide

This document covers everything required to run Notaria Notary safely in production.

## Pre-flight checklist

- [ ] Copy `.env.example` to `.env` and fill in all production values
- [ ] `DJANGO_DEBUG=false`
- [ ] Strong `DJANGO_SECRET_KEY` (never commit or reuse across environments)
- [ ] PostgreSQL via `DATABASE_URL` (do not use SQLite in production)
- [ ] `SITE_URL` set to your public HTTPS URL (no trailing slash)
- [ ] `DJANGO_ALLOWED_HOSTS` includes your domain(s)
- [ ] `CSRF_TRUSTED_ORIGINS` includes your HTTPS origin(s)
- [ ] SMTP email configured
- [ ] Run `python manage.py migrate`
- [ ] Run `python manage.py collectstatic --noinput`
- [ ] Create staff users and seed service types
- [ ] Reverse proxy terminates TLS and sets `X-Forwarded-Proto`
- [ ] Persistent volume for `media/`
- [ ] Backups for PostgreSQL and media
- [ ] Verify `GET /health/` returns OK

## Minimum production `.env`

```env
DJANGO_SECRET_KEY=<generate-a-long-random-key>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=notary.example.com
SITE_URL=https://notary.example.com
CSRF_TRUSTED_ORIGINS=https://notary.example.com
DATABASE_URL=postgres://user:pass@host:5432/notary
CONTACT_EMAIL=office@notary.example.com
DEFAULT_FROM_EMAIL=noreply@notary.example.com
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
EMAIL_USE_TLS=true
USE_PROXY_SSL_HEADER=true
```

See [.env.example](.env.example) for the full variable list.

## Railway

1. Create a **PostgreSQL** service in the same project.
2. In your **web service** → **Variables**, reference the database URL:
   - Add variable `DATABASE_URL` → value `${{Postgres.DATABASE_URL}}`  
     (use your Postgres service name if different)
3. Do **not** set `DATABASE_URL` to an empty string — that overrides the linked value.
4. Set at minimum:
   ```env
   DJANGO_DEBUG=false
   DJANGO_SECRET_KEY=<long-random-key>
   DJANGO_ALLOWED_HOSTS=your-app.up.railway.app
   SITE_URL=https://your-app.up.railway.app
   CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app
   ```
5. Redeploy. Migrations run via `scripts/entrypoint.sh` on startup.

**Quick demo without Postgres:** set `USE_SQLITE=true` (ephemeral — data resets on redeploy unless you attach persistent storage).

## Coolify

Coolify runs your app in a **disposable container**. Anything written inside the container (SQLite file, uploads) is **deleted on every redeploy or restart** unless you attach persistent storage.

### Recommended: PostgreSQL

1. Add a **PostgreSQL** database in Coolify and copy its connection URL.
2. Set on your app:
   ```env
   DJANGO_DEBUG=false
   DATABASE_URL=postgres://user:pass@host:5432/notary
   DJANGO_SECRET_KEY=<long-random-key>
   DJANGO_ALLOWED_HOSTS=notary.gammaan.com
   SITE_URL=https://notary.gammaan.com
   CSRF_TRUSTED_ORIGINS=https://notary.gammaan.com
   ```
3. Use the **Dockerfile** build (not a bare Procfile start command).
4. Start command: `./scripts/entrypoint.sh` (runs migrations + collectstatic, then Gunicorn).

PostgreSQL keeps your data across redeploys. Static CSS/JS is baked into the Docker image at build time.

### SQLite demo (with persistence)

If you use `USE_SQLITE=true`, mount a **persistent volume**:

| Container path | Purpose |
|----------------|---------|
| `/data` | SQLite database (`db.sqlite3`) and `media/` uploads |

Set `DATA_DIR=/data` in your environment variables.

Without the volume, every redeploy gives you an empty database (causing errors like `no such table: cms_post`) and no uploaded files.

### Why styles disappear

Static files live in `staticfiles/` inside the container. If Coolify starts Gunicorn directly (skipping `entrypoint.sh`) and does not run `collectstatic` during the Docker build, CSS/JS return 404 after redeploy. The Dockerfile now runs `collectstatic` at build time; `entrypoint.sh` runs it again on startup as a safety net.

## Static and media

- **Static** — collected to `staticfiles/`; served by WhiteNoise or nginx
- **Media** — user uploads in `media/`; serve via nginx (see `scripts/nginx.conf.example`)

## Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
```

Or use `Procfile`, `scripts/entrypoint.sh`, or Docker Compose.

## Docker Compose

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_service_types
```

## Security (when `DJANGO_DEBUG=false`)

- HTTPS redirect, secure cookies, HSTS
- Required secret key, database URL, and site URL
- Proxy SSL header support for reverse proxies

Run before go-live:

```bash
DJANGO_DEBUG=false python manage.py check --deploy
```

## Health check

`GET /health/` — JSON status with database connectivity.
