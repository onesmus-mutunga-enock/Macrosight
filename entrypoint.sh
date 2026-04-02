#!/bin/sh
set -e

echo "Starting MacroSight Backend..."

# Only run Django setup for web service
if [ "$1" = "gunicorn" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput

  echo "Collecting static files..."
  python manage.py collectstatic --noinput

  echo "Django system check..."
  python manage.py check
fi

exec "$@"