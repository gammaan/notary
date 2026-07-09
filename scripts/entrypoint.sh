#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-/app}"
mkdir -p "$DATA_DIR" "$DATA_DIR/media"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
exec gunicorn config.wsgi:application \
  --bind "${GUNICORN_BIND:-0.0.0.0:${PORT}}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
