import os
import sys
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if it exists
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-secret-key-grainlab-2026")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
MOCK_MODE = os.getenv("MOCK_MODE", "True").lower() in ("true", "1", "t")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",  # Our custom core baking engine logic
]

MIDDLEWARE = [
    "apps.core.middleware.CorrelationIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.MaintenanceModeMiddleware",
]

ROOT_URLCONF = "grainlab.urls"

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
                "apps.core.context_processors.system_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "grainlab.wsgi.application"

# Database configuration: support discrete variables or DATABASE_URL (PostgreSQL)
# Fallback to local SQLite if neither is configured (e.g. local offline development).
DATABASE_URL = os.getenv("DATABASE_URL")
db_name = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME")
db_user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER")
db_password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
db_host = os.getenv("DATABASE_HOST") or os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST")
raw_port = os.getenv("DATABASE_PORT") or os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT", "5432")

try:
    default_db_port = int(raw_port)
except (ValueError, TypeError):
    default_db_port = 5432

if DATABASE_URL:
    url = urllib.parse.urlparse(DATABASE_URL)
    try:
        parsed_port = url.port or default_db_port
    except (ValueError, TypeError):
        parsed_port = default_db_port
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": url.path.lstrip("/"),
            "USER": urllib.parse.unquote(url.username) if url.username else (db_user or "grainlab_user"),
            "PASSWORD": urllib.parse.unquote(url.password) if url.password else (db_password or ""),
            "HOST": url.hostname or (db_host or "db"),
            "PORT": parsed_port,
        }
    }
elif db_host or db_name:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name or "grainlab",
            "USER": db_user or "grainlab_user",
            "PASSWORD": db_password or "",
            "HOST": db_host or "db",
            "PORT": default_db_port,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CSRF settings for reverse proxies:
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Dynamically add the configured local port
local_port = os.getenv("LOCAL_PORT")
if local_port:
    CSRF_TRUSTED_ORIGINS.extend(
        [
            f"http://localhost:{local_port}",
            f"http://127.0.0.1:{local_port}",
        ]
    )

# Allow trusted origins overrides via environment variables
env_csrf = os.getenv("CSRF_TRUSTED_ORIGINS")
if env_csrf:
    CSRF_TRUSTED_ORIGINS.extend([o.strip() for o in env_csrf.split(",") if o.strip()])

# Recognize headers from SSL-terminating reverse proxies
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Create logs directory if it does not exist
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# Cookie security settings
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Enforce secure cookies flags only if not in debug
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# Structured logger system with request correlation ID tracking for Loki & Prometheus
APP_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {
            "()": "apps.core.middleware.CorrelationIDFilter",
        },
    },
    "formatters": {
        "json": {
            "()": "apps.core.middleware.LokiJsonFormatter",
        },
        "standard": {
            "format": "[%(asctime)s] [%(correlation_id)s] [%(name)s:%(levelname)s] - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["correlation_id"],
            "formatter": "standard" if os.environ.get("CONSOLE_PRETTY", "").lower() in ("true", "1") else "json",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": logs_dir / "grainlab.log",
            "filters": ["correlation_id"],
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": APP_LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "grainlab": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
        "apps.core": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
    },
}

# Persistent cache backend
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TASK_ALWAYS_EAGER = "test" in sys.argv  # Execute synchronously in tests

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
