#!/bin/sh
# Honor Board container entrypoint: migrate, maybe create the superuser, serve.
set -e

echo "==> Honor Board: applying database migrations"
python manage.py migrate --noinput

# Create the initial superuser non-interactively. Runs only when
# DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD are set, and only
# when the user does not exist yet -- so restarts never fail.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python - <<'PY'
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip() or None
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

if User.objects.filter(username=username).exists():
    print(f"==> Honor Board: superuser '{username}' already exists, skipping")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"==> Honor Board: superuser '{username}' created")
PY
fi

echo "==> Honor Board: starting Gunicorn on 0.0.0.0:8000"
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --log-file - \
    --access-logfile -
