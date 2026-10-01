"""
WSGI config for the Honor Board project.

Exposes the WSGI callable as a module-level variable named ``application``.
Gunicorn (entrypoint.sh) serves this.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
