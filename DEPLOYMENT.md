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

### Build pack and start command (important)

Nixpacks often **guesses the wrong WSGI module** (e.g. `gammaan.wsgi` from the GitHub org name). This project uses **`config.wsgi:application`**.

If you see `ModuleNotFoundError: No module named 'gammaan'`:

1. Open your app in Coolify → **General** → **Start Command**
2. Set it to: `bash scripts/entrypoint.sh`
3. Clear any custom command like `gunicorn gammaan.wsgi:application`
4. Redeploy

**Better:** switch the build pack to **Dockerfile** (uses our `Dockerfile` + `ENTRYPOINT` automatically).

The repo includes `nixpacks.toml` so Nixpacks builds also use the correct start command.

**Correct start command** (paste in Coolify → General → Start Command):

```bash
bash scripts/entrypoint.sh
```

Or inline:

```bash
python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120 --access-logfile - --error-logfile -
```

### PostgreSQL on Coolify (recommended)

SQLite inside the app container is **wiped on every redeploy**. Use a separate **PostgreSQL** service so database data survives restarts. This project supports PostgreSQL out of the box (`DATABASE_URL` in settings); MySQL is not configured.

#### Checklist

- [ ] Create a **PostgreSQL** database service in the same Coolify project
- [ ] Copy the **internal** connection URL from the database service (host is usually the DB container name, not `localhost`)
- [ ] In the **web app** → **Environment Variables**, set `DATABASE_URL` (see below)
- [ ] **Remove** `USE_SQLITE=true` if it is set
- [ ] **Remove** any empty `DATABASE_URL=` variable that would override a linked value
- [ ] Set production vars: `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `SITE_URL`, `CSRF_TRUSTED_ORIGINS`
- [ ] Build pack: **Dockerfile** (recommended) or Nixpacks with start command `bash scripts/entrypoint.sh`
- [ ] Mount a persistent volume at **`/app/data`** and set `DATA_DIR=/app/data` for user uploads (avatars, documents)
- [ ] Redeploy — `entrypoint.sh` runs `migrate` automatically on startup
- [ ] Run once on the new database: `python manage.py createsuperuser` and `python manage.py seed_service_types`
- [ ] Verify `GET /health/` returns OK

#### Environment variables

```env
DJANGO_DEBUG=false
DATABASE_URL=postgres://postgres:YOUR_PASSWORD@YOUR_DB_HOST:5432/notary
DJANGO_SECRET_KEY=<long-random-key>
DJANGO_ALLOWED_HOSTS=notary.gammaan.com
SITE_URL=https://notary.gammaan.com
CSRF_TRUSTED_ORIGINS=https://notary.gammaan.com
DATA_DIR=/app/data
```

Coolify often provides a URL ending in `/postgres`. Change the database name to `/notary`, or create a `notary` database in Postgres first.

If Coolify supports referencing the database service, you can link it (adjust the service name if different):

```env
DATABASE_URL=postgres://postgres:password@your-postgres-container:5432/notary
```

#### After switching from SQLite

PostgreSQL starts **empty**. You must recreate staff users and seed data. Existing SQLite data is not migrated automatically.

Run via Coolify **Execute Command** on the web container:

```bash
python manage.py createsuperuser
python manage.py seed_service_types
```

#### What persists where

| Data | Storage | Survives redeploy? |
|------|---------|-------------------|
| Users, matters, clients, CMS | PostgreSQL service | Yes |
| Staff avatars, uploaded documents | `/app/data/media` volume | Yes (if volume mounted) |
| Static CSS/JS | Baked into Docker image + `collectstatic` | Yes |
| SQLite in container | `/app/data/db.sqlite3` | Only with volume; not for production |

#### Start command

Use the **Dockerfile** build pack (uses `ENTRYPOINT` automatically), or set **Start Command** to:

```bash
bash scripts/entrypoint.sh
```

### SQLite demo (not for production)

If you use `USE_SQLITE=true`, mount a **persistent volume**:

| Container path | Purpose |
|----------------|---------|
| `/app/data` | SQLite database (`db.sqlite3`) and `media/` uploads |

Set `DATA_DIR=/app/data` in your environment variables (this is the default).

Do **not** use `/data` unless you mount and permission that path yourself. Coolify/Nixpacks often make `/app` read-only, so the database cannot live in `/app/db.sqlite3`.

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
