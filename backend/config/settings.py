"""
Vector Strike — Django settings.

The default local configuration uses SQLite so the project runs on any machine
with zero external services. PostgreSQL is fully supported and enabled by
setting DB_ENGINE=postgres (see .env.example). No secrets are committed.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-secret-key-change-me-in-production",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # Vector Strike applications
    "apps.accounts",
    "apps.profiles",
    "apps.games",
    "apps.tournaments",
    "apps.challenges",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL-ready with a SQLite local fallback.
# ---------------------------------------------------------------------------
DB_ENGINE = os.environ.get("DB_ENGINE", "").lower().strip()

if DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "vector_strike"),
            "USER": os.environ.get("POSTGRES_USER", "vector_strike"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "vector_strike"),
            "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# ---------------------------------------------------------------------------
# JWT — short-lived access tokens + longer-lived rotating refresh tokens.
# The refresh token is stored by the backend in an HttpOnly cookie so it never
# passes through JavaScript; access tokens are returned in bodies and kept in
# memory by the frontend. Refresh-token rotation + blacklisting provide
# server-side revocation on logout.
# ---------------------------------------------------------------------------
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

JWT_REFRESH_COOKIE = os.environ.get("JWT_REFRESH_COOKIE", "vs_refresh")
JWT_REFRESH_COOKIE_PATH = "/api/v1/auth/"

# ---------------------------------------------------------------------------
# Email & phone verification configuration
# ---------------------------------------------------------------------------
# Development default writes e-mail to the console; production deployments set
# EMAIL_BACKEND (e.g. django.core.mail.backends.smtp.EmailBackend) via env.
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@vectorstrike.app")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://127.0.0.1:5173")

# Phone / SMS provider. "console" is the isolated development behaviour that
# merely logs the OTP; production must set PHONE_VERIFICATION_PROVIDER to a
# real SMS provider adapter before it can send.
PHONE_VERIFICATION_PROVIDER = os.environ.get("PHONE_VERIFICATION_PROVIDER", "console")
PHONE_OTP_LIFETIME_MINUTES = int(os.environ.get("PHONE_OTP_LIFETIME_MINUTES", "10"))
PHONE_OTP_MAX_ATTEMPTS = int(os.environ.get("PHONE_OTP_MAX_ATTEMPTS", "5"))

# One-time token lifetimes.
EMAIL_VERIFICATION_TOKEN_HOURS = int(os.environ.get("EMAIL_VERIFICATION_TOKEN_HOURS", "24"))
PASSWORD_RESET_TOKEN_HOURS = int(os.environ.get("PASSWORD_RESET_TOKEN_HOURS", "24"))

# Profile starting values for brand-new accounts. Genuine starting state —
# no fabricated gameplay statistics.
PROFILE_STARTING_LEVEL = int(os.environ.get("PROFILE_STARTING_LEVEL", "1"))
PROFILE_STARTING_XP = int(os.environ.get("PROFILE_STARTING_XP", "0"))
PROFILE_STARTING_RANK = os.environ.get("PROFILE_STARTING_RANK", "rookie")

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "register": "10/min",
        "login": "10/min",
        "username": "30/min",
        "upload": "10/min",
        "anon": "120/min",
        "email_verify": "10/min",
        "email_resend": "3/min",
        "phone": "6/min",
        "password_reset": "5/min",
    },
    "EXCEPTION_HANDLER": "apps.accounts.exceptions.api_exception_handler",
}

# ---------------------------------------------------------------------------
# CORS / CSRF — development credentials policy (Vite dev proxy + direct origin).
# ---------------------------------------------------------------------------
_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",") if o
] or _CORS_ORIGINS

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# Vector Strike account rules
# ---------------------------------------------------------------------------
# The ages below are thresholds, kept in one configurable place.
MINIMUM_ACCOUNT_AGE = 6  # Years.
GUARDIAN_AGE_THRESHOLD = 17  # Users younger than this require a guardian.
VERIFICATION_AGE_THRESHOLD = 17  # Users this age or older go through verification.
MINIMUM_ONBOARDING_INTERESTS = 3
# If True, accounts at/above VERIFICATION_AGE_THRESHOLD must verify their age
# before activation. Set per region below.
REQUIRE_AGE_VERIFICATION = True
# Map of ISO country code -> required verification. "default" applies when the
# user does not specify a region.
AGE_VERIFICATION_REGION_CONFIG = {
    "default": {"required": True, "min_age": 17, "methods": ["document"]},
    "US": {"required": True, "min_age": 17, "methods": ["document", "provider"]},
    "EU": {"required": True, "min_age": 16, "methods": ["document"]},
    "IN": {"required": False, "min_age": 17, "methods": []},
}

# ---------------------------------------------------------------------------
# Secure file storage for identity verification documents.
# Documents are stored outside the user table in a dedicated directory.
# ---------------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "secure_storage"
VERIFICATION_UPLOAD_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
VERIFICATION_UPLOAD_EXPIRY_DAYS = 1

# ---------------------------------------------------------------------------
# Internationalization & static
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"