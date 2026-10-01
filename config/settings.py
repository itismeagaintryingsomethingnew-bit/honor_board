"""
Django settings for the Honor Board (لوحة الشرف) project.

Everything deployment-specific arrives through environment variables so the
exact same code runs locally (SQLite + local media) and on SnapDeploy
(PostgreSQL/Neon + Cloudinary + WhiteNoise + Gunicorn).

Environment variables used:

    SECRET_KEY                long random string; required when DEBUG is False
    DEBUG                     "True" / "False" (default: False)
    ALLOWED_HOSTS             comma separated, e.g. "app.snapdeploy.app,site.com"
    CSRF_TRUSTED_ORIGINS      comma separated with scheme, e.g. "https://app.snapdeploy.app"
    DATABASE_URL              PostgreSQL URL (Neon). Empty -> local SQLite.
    CLOUDINARY_URL            cloudinary://api_key:api_secret@cloud_name. Empty -> local media/.

    DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD
                              used once by entrypoint.sh to create the admin user.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Local .env support (development convenience only)
# ---------------------------------------------------------------------------
def _load_local_env(path):
    """Read a .env file (KEY=VALUE lines) without any external dependency.

    Local development convenience only: the production container receives
    real environment variables and .env is excluded from the Docker image,
    so this is a no-op there. Real environment variables always win.
    """
    if not path.is_file():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env(BASE_DIR / ".env")


def env_bool(name, default="False"):
    """Read a boolean-ish environment variable."""
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def env_list(name):
    """Read a comma-separated environment variable into a clean list."""
    return [part.strip() for part in os.environ.get(name, "").split(",") if part.strip()]


# ---------------------------------------------------------------------------
# Core security
# ---------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", default="False")

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        # Development-only fallback; production always provides the env var.
        SECRET_KEY = "django-insecure-development-only-key"
    else:
        raise ImproperlyConfigured(
            "The SECRET_KEY environment variable is required when DEBUG is False "
            "(the Docker build step passes a throwaway value for collectstatic)."
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    # Sensible defaults: localhost for development, the platform domain for
    # production. Set ALLOWED_HOSTS explicitly when using a custom domain.
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"] if DEBUG else [".snapdeploy.app"]

# Origins allowed to submit forms (admin login) through the HTTPS proxy.
# A scheme is required, so one is added if the value was written without it.
CSRF_TRUSTED_ORIGINS = [
    origin if "://" in origin else f"https://{origin}"
    for origin in env_list("CSRF_TRUSTED_ORIGINS")
]
if not CSRF_TRUSTED_ORIGINS and not DEBUG:
    # Out of the box, the admin login works on the platform's *.snapdeploy.app
    # domain. Add your custom domain here when you have one.
    CSRF_TRUSTED_ORIGINS = ["https://*.snapdeploy.app"]


# ---------------------------------------------------------------------------
# Applications and middleware
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Serves static files through WhiteNoise under runserver too, so local
    # development behaves exactly like production.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "board",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# PostgreSQL (Neon) when DATABASE_URL is set, SQLite for local development.
# Neon quirks: force SSL, keep connections warm (conn_max_age) and health-check
# them, because the database can be asleep when a cold container receives its
# first request.
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=60,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------------
# Internationalization (the whole site and admin are in Arabic)
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "ar"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files (WhiteNoise) and media (Cloudinary or local)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", "")

STORAGES = {
    # Student photos: Cloudinary when configured (the container filesystem is
    # ephemeral), otherwise a local media/ folder so development just works.
    "default": {
        "BACKEND": (
            "config.cloudinary_storage.CloudinaryMediaStorage"
            if CLOUDINARY_URL
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    # Hashed + compressed static files in production; plain storage in DEBUG so
    # runserver picks up edits immediately.
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}


# ---------------------------------------------------------------------------
# Security hardening behind the platform's HTTPS reverse proxy
# ---------------------------------------------------------------------------
if not DEBUG:
    # SnapDeploy terminates TLS and forwards to the container over HTTP.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Note: SECURE_SSL_REDIRECT is intentionally not enabled so the /health/
    # endpoint keeps answering 200 directly (the platform enforces HTTPS at
    # its edge anyway).


# ---------------------------------------------------------------------------
# Password validation and logging
# ---------------------------------------------------------------------------
# The only interactive area is the admin, so log straight into it.
LOGIN_REDIRECT_URL = "/admin/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
