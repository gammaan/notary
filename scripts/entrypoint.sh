#!/usr/bin/env bash
set -euo pipefail

export DATA_DIR="${DATA_DIR:-/app/data}"
export MEDIA_ROOT="${MEDIA_ROOT:-$DATA_DIR/media}"

mkdir -p "$DATA_DIR" "$MEDIA_ROOT"

if ! touch "$DATA_DIR/.write-test" 2>/dev/null; then
  echo "ERROR: DATA_DIR ($DATA_DIR) is not writable by $(whoami)." >&2
  echo "Mount a persistent volume at /app/data or fix volume permissions." >&2
  exit 1
fi
rm -f "$DATA_DIR/.write-test"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
exec gunicorn config.wsgi:application \
  --bind "${GUNICORN_BIND:-0.0.0.0:${PORT}}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
