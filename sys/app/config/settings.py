from pathlib import Path

from .env import get_bool, get_int, get_list, get_text

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = get_text("DJANGO_SECRET_KEY", "demo03-am-local-development-secret-key")
DEBUG = get_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = get_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "0.0.0.0"])
CSRF_TRUSTED_ORIGINS = get_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "assets",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.PortalSessionMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_text("POSTGRES_DB", "demo03_am"),
        "USER": get_text("POSTGRES_USER", "demo03_am"),
        "PASSWORD": get_text("POSTGRES_PASSWORD", "demo03_am"),
        "HOST": get_text("POSTGRES_HOST", "tdev-demo03-db"),
        "PORT": get_int("POSTGRES_PORT", 5432),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

SESSION_COOKIE_NAME = get_text("SESSION_COOKIE_NAME", "demo03_am_session")
LOGIN_URL = "/auth/handover"

AUTH_MODE = get_text("AUTH_MODE", "dev-header")
PORTAL_COOKIE_NAME = get_text("PORTAL_COOKIE_NAME", "portal_token")
PORTAL_COOKIE_NAMES = get_list("PORTAL_COOKIE_NAMES", [PORTAL_COOKIE_NAME])
PORTAL_ISSUER = get_text("PORTAL_ISSUER", "")
PORTAL_JWKS_URL = get_text("PORTAL_JWKS_URL", "")
PORTAL_LOGIN_URL = get_text("PORTAL_LOGIN_URL", "")
PORTAL_ALLOWED_RETURN_TO_HOSTS = get_list(
    "PORTAL_ALLOWED_RETURN_TO_HOSTS",
    ["localhost:18003", "127.0.0.1:18003"],
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
