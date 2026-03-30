from pathlib import Path
import os
from datetime import timedelta
import logging

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-secret-key-change-me")

ENVIRONMENT = os.getenv("DJANGO_ENV", "dev").lower()
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    "django_extensions",
    "django_celery_results",
    "django_celery_beat",
    # "django_prometheus",
    "health_check",
    "django_elasticsearch_dsl",
    "django_elasticsearch_dsl_drf",
]

LOCAL_APPS=[
    "apps.audit",
    "apps.ml",
    "apps.forecasts",
    

    "apps.users",
    "apps.governance",
    "apps.policies",
    "apps.indicators",
    "apps.sectors",
    "apps.costs",
    "apps.sales",
    "apps.products",
    "apps.scenarios",
    "apps.system",
    "apps.inputs",
    "apps.notices",
    "apps.dashboard",
    "apps.agriculture_inputs",
    "apps.externalindicator",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

        
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "macrosight.urls"

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

WSGI_APPLICATION = "macrosight.wsgi.application"
ASGI_APPLICATION = "macrosight.asgi.application"

if ENVIRONMENT == "prod":
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
            "NAME": os.getenv("DJANGO_DB_NAME", "macrosight"),
            "USER": os.getenv("DJANGO_DB_USER", "macrosight"),
            "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", ""),
            "HOST": os.getenv("DJANGO_DB_HOST", "localhost"),
            "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.getenv("DJANGO_DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {
                "connect_timeout": 10,
                "sslmode": "require",
                "sslrootcert": os.getenv("DJANGO_DB_SSL_ROOT_CERT", ""),
                "sslcert": os.getenv("DJANGO_DB_SSL_CERT", ""),
                "sslkey": os.getenv("DJANGO_DB_SSL_KEY", ""),
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "30"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": os.getenv("JWT_ALGORITHM", "HS256"),
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MacroSight API",
    "DESCRIPTION": "MacroSight V1 economic intelligent,forecasting and governance platform API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "CONTACT": {"name": "MacroSight Platform lead"},
    "LICENSE": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    "TERMS_OF_SERVICE": "https://macrosight.com/terms/",
    "EXTERNAL_DOCS": {
        "description": "Additional Documentation",
        "url": "https://docs.macrosight.com/"
    },
}

# Celery beat schedules for external data ingestion (example schedules)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Ingest a couple of common World Bank indicators daily at 02:00 UTC
    "ingest_world_bank_gdp": {
        "task": "apps.externalindicator.tasks.task_ingest_world_bank",
        "schedule": crontab(hour=2, minute=0),
        "args": ["NY.GDP.MKTP.CD", "KEN"],
    },
    "ingest_world_bank_inflation": {
        "task": "apps.externalindicator.tasks.task_ingest_world_bank",
        "schedule": crontab(hour=2, minute=30),
        "args": ["FP.CPI.TOTL.ZG", "KEN"],
    },
    # Placeholder central bank ingest - daily at 03:00 UTC (configure endpoint)
    "ingest_central_bank_rates": {
        "task": "apps.externalindicator.tasks.task_ingest_central_bank",
        "schedule": crontab(hour=3, minute=0),
        "args": ["Central Bank of Kenya", "https://www.centralbank.go.ke/api/rates"],
    },
}

CELERY_TIMEZONE = "UTC"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
)
CELERY_TASK_ALWAYS_EAGER = os.getenv(
    "CELERY_TASK_ALWAYS_EAGER", "False"
).lower() == "true"
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "900"))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "600"))

# Celery queues and routing
CELERY_TASK_DEFAULT_QUEUE = os.getenv("CELERY_DEFAULT_QUEUE", "default")
CELERY_TASK_ROUTES = {
    # Training jobs go to training_queue
    "apps.ml.tasks.run_training_job": {"queue": "training_queue"},
    # Forecast computations go to forecast_queue
    "apps.forecasts.tasks.run_forecast_task": {"queue": "forecast_queue"},
    # Monitoring/orchestration tasks go to monitoring_queue
    "apps.forecasts.tasks.run_forecast_schedule": {"queue": "monitoring_queue"},
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 5,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "celery": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "celery.log",
            "maxBytes": 1024 * 1024 * 5,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
        "celery": {
            "handlers": ["celery"],
            "level": "INFO",
        },
    },
}

# Prometheus monitoring
PROMETHEUS_EXPORT_MIGRATIONS = True
PROMETHEUS_WSGI_MIDDLEWARE_ENABLED = True

# Health check configuration
HEALTH_CHECK = {
    "allowed_hosts": ["localhost", "127.0.0.1"],
    "checks": {
        "database": {"django.db.backends"},
        "celery": {"django_celery_results"},
        "redis": {"redis"},
    }
}

# Elasticsearch configuration
ELASTICSEARCH_DSL = {
    "default": {
        "hosts": os.getenv("ELASTICSEARCH_HOSTS", "localhost:9200"),
        "timeout": 20,
        "max_retries": 3,
    }
}

# Database optimization settings
DATABASE_OPTIONS = {
    "conn_max_age": 60,
    "options": {
        "connect_timeout": 10,
        "sslmode": "require",
    }
}

# Security settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",

]

CORS_ALLOW_CREDENTIALS = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = ENVIRONMENT == "prod"
CSRF_COOKIE_SECURE = ENVIRONMENT == "prod"
X_FRAME_OPTIONS = "DENY"

# Performance optimization
CACHE_BACKEND = "django.core.cache.backends.redis.RedisCache"
CACHE_LOCATION = os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/1")
CACHE_TIMEOUT = 300  # 5 minutes

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"