from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com"
    ).split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dashboard",
    "institutional",
    "gestao.apps.GestaoConfig",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# SQLite continua útil no desenvolvimento local. Em produção, DATABASE_URL deve
# apontar para PostgreSQL persistente (ex.: Supabase/Postgres).
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": dj_database_url.parse(
            f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Autenticação / gestão
LOGIN_URL = "gestao:login"
LOGIN_REDIRECT_URL = "gestao:dashboard"
LOGOUT_REDIRECT_URL = "institutional:home"
PASSWORD_RESET_TIMEOUT = int(os.getenv("PASSWORD_RESET_TIMEOUT", "3600"))
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", str(8 * 60 * 60)))
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
GESTOR_CRITICAL_ACTION_SECRET_HASH = os.getenv(
    "GESTOR_CRITICAL_ACTION_SECRET_HASH", ""
)

# E-mail: console no desenvolvimento até SMTP ser configurado.
EMAIL_HOST = os.getenv("EMAIL_HOST", "").strip()
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend",
)
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Projeto Nutri na Escola <nao-responda@localhost>",
)

# Dados analíticos
DATA_DIR = Path(os.getenv("CAAFE_DATA_DIR", BASE_DIR / "data"))
CAAFE_LOCAL_CSV = Path(
    os.getenv("CAAFE_LOCAL_CSV", DATA_DIR / "caafe_dashboard.csv")
)
CAAFE_PARQUET_PATH = Path(
    os.getenv("CAAFE_PARQUET_PATH", DATA_DIR / "cache" / "caafe_dashboard.parquet")
)
CAAFE_METADATA_PATH = Path(
    os.getenv("CAAFE_METADATA_PATH", DATA_DIR / "cache" / "source_metadata.json")
)
CAAFE_SCHOOL_LOCATIONS = Path(
    os.getenv("CAAFE_SCHOOL_LOCATIONS", DATA_DIR / "school_locations.csv")
)
CAAFE_REFRESH_SECONDS = int(os.getenv("CAAFE_REFRESH_SECONDS", "3600"))
CAAFE_SCHOOLS_REFRESH_SECONDS = int(
    os.getenv("CAAFE_SCHOOLS_REFRESH_SECONDS", "86400")
)
CAAFE_SCHOOLS_LOCAL_CSV = Path(
    os.getenv("CAAFE_SCHOOLS_LOCAL_CSV", DATA_DIR / "escolas.csv")
)
CAAFE_SCHOOLS_PARQUET_PATH = Path(
    os.getenv("CAAFE_SCHOOLS_PARQUET_PATH", DATA_DIR / "cache" / "escolas.parquet")
)
CAAFE_SCHOOLS_METADATA_PATH = Path(
    os.getenv("CAAFE_SCHOOLS_METADATA_PATH", DATA_DIR / "cache" / "schools_metadata.json")
)

# Supabase Storage
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "projeto_saude_alimentar")
SUPABASE_OBJECT_PATH = os.getenv("SUPABASE_OBJECT_PATH", "data.csv")
SUPABASE_SCHOOLS_OBJECT_PATH = os.getenv("SUPABASE_SCHOOLS_OBJECT_PATH", "escolas.csv")
SUPABASE_MEDIA_BUCKET = os.getenv("SUPABASE_MEDIA_BUCKET", "saude-alimentar-media")

DATA_REFRESH_TOKEN = os.getenv("DATA_REFRESH_TOKEN", "")
CAAFE_MODEL_MODE = os.getenv("CAAFE_MODEL_MODE", "validated").lower()

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(DATA_DIR / "cache" / "django"),
        "TIMEOUT": CAAFE_REFRESH_SECONDS,
        "OPTIONS": {"MAX_ENTRIES": 300},
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        }
    },
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
