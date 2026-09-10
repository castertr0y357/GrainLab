#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# If DATABASE_URL is defined, wait for database container to be reachable
if [ -n "$DATABASE_URL" ]; then
  echo "Checking database connection..."
  until python -c "
import sys, urllib.parse, socket
url = urllib.parse.urlparse('$DATABASE_URL')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((url.hostname, url.port or 5432))
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
    echo "Database is unavailable - sleeping"
    sleep 2
  done
  echo "Database is ready!"
fi

# Apply database migrations
echo "Applying migrations..."
python manage.py migrate --noinput

# Seed database and bootstrap superuser
if [ "$AUTO_SEED_DB" = "True" ] || [ "$AUTO_SEED_DB" = "true" ] || [ "$AUTO_SEED_DB" = "1" ]; then
  echo "Seeding database and superuser..."
  python manage.py seed_db
else
  echo "Skipping database seeding (AUTO_SEED_DB is not enabled)."
fi

# Execute the container's main command
echo "Executing CMD: $@"
exec "$@"
