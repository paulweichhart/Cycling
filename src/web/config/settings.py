"""Django settings for the VO2max web page.

The page has no database: the form is evaluated and shown, nothing is stored.
For production set DJANGO_SECRET_KEY, DJANGO_DEBUG=0 and DJANGO_ALLOWED_HOSTS.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # src/web

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,cycling-api-ol1z.onrender.com,cycling.paulweichhart.com").split(",")
# full origins, e.g. "https://vo2max.example.com", needed for the form POST behind HTTPS
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "https://cycling.paulweichhart.com").split(",") if o]
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):  # set by Render
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

# the FastAPI service in src/service; the timeout covers a sleeping free Render instance
VO2MAX_SERVICE_URL = os.environ.get("VO2MAX_SERVICE_URL", "https://cycling-api-ol1z.onrender.com")
VO2MAX_SERVICE_TIMEOUT = float(os.environ.get("VO2MAX_SERVICE_TIMEOUT", "60"))

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "predictor",
    "django_tailwind_cli",
]

STATICFILES_DIRS = [BASE_DIR / "assets"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic target, served by WhiteNoise
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
