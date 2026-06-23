#!/bin/sh
set -eu

if [ "${POSTGRES_HOST:-}" ]; then
  until nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
    echo "Waiting for PostgreSQL..."
    sleep 1
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
