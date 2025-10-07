from dotenv import load_dotenv
import os

from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG") == "True"

TELEGRAM_BOT_TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN_TEST") if DEBUG else os.getenv("TELEGRAM_BOT_TOKEN")
)

# ======================
# HOSTS & DOMAINS
# ======================
FRONTEND_DEV_URL = "http://localhost:3000"
FRONTEND_PROD_URL = "https://kiberonetgbot.online"

ALLOWED_HOSTS = [
    "kiberonetgbot.online",
    "www.kiberonetgbot.online",
    "93.85.88.72",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

# ======================
# CORS (для разработки и продакшена)
# ======================

CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    # В разработке — разрешаем localhost:3000
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:8000",
        "http://0.0.0.0:3000",
    ]
else:
    # В продакшене — разрешаем и продакшен-фронтенд, и localhost для разработки
    CORS_ALLOWED_ORIGINS = [
        "https://kiberonetgbot.online",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:8000",
    ]

# ======================
# CSRF
# ======================
CSRF_TRUSTED_ORIGINS = [
    "https://kiberonetgbot.online",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Безопасные cookies
SESSION_COOKIE_SECURE = not DEBUG  # True в продакшене (HTTPS), False в dev
CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_HTTPONLY = True


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # DRF
    "rest_framework",
    # Swagger
    "drf_yasg",
    # Celery
    "django_celery_results",
    "django_celery_beat",
    # Apps
    "app_api",
    "app_kiberclub",
    "app_kibershop.apps.AppKibershopConfig",
    "app_clients_resumes",
    # CORS
    'corsheaders',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = "_web_service.urls"

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
                "app_kibershop.context_processors.cart",
                "app_kibershop.context_processors.get_user_kiberons",
            ],
        },
    },
]

WSGI_APPLICATION = "_web_service.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Разрешаем доступ без аутентификации
    ],
}


LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "Europe/Moscow"

USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
if DEBUG:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]
else:
    STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Настройки Celery
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Moscow"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
# Хранение результатов задач в базе данных Django
CELERY_RESULT_BACKEND = "django-db"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {filename} {lineno} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {filename} {lineno} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "debug.log"),
            "maxBytes": 1024 * 1024,  # 1 Мегабайт
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "app_api": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "app_kiberclub": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
