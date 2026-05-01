"""
Django settings for visitas_corporativas project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis de ambiente do arquivo .env (desenvolvimento local)
load_dotenv(BASE_DIR.parent / ".env")

# ---------------------------------------------------------------------------
# Segurança
# ---------------------------------------------------------------------------
DEBUG = os.environ.get("DEBUG", "True") == "True"

# Em produção (DEBUG=False), SECRET_KEY deve estar na variável de ambiente
_default_secret = "django-insecure-4tse_b7fs7lzkl4uq2vjj1qhucu^91qkmb$^k+$_a89h$^%0tq"
SECRET_KEY = os.environ.get("SECRET_KEY", _default_secret if DEBUG else None)
if not SECRET_KEY:
    raise Exception("❌ Defina a variável de ambiente SECRET_KEY em produção!")

ALLOWED_HOSTS = ["*"]

# O Railway injeta RAILWAY_PUBLIC_DOMAIN automaticamente em cada environment.
# Assim staging e production funcionam sem precisar hardcodar a URL.
_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8081",
    "https://*.ngrok-free.app",
    "https://*.loca.lt",
]
if _railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_railway_domain}")

# ---------------------------------------------------------------------------
# Aplicações instaladas
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # App principal
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "visitaPro.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.parent / "frontend" / "templates"],
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

WSGI_APPLICATION = "visitaPro.wsgi.application"

# ---------------------------------------------------------------------------
# Banco de Dados — APENAS PostgreSQL (Google Cloud ou Railway)
# Obrigatório: variável de ambiente DATABASE_URL deve estar configurada.
# ---------------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception(
        "❌ A variável de ambiente DATABASE_URL não está configurada!\n"
        "Configure-a no arquivo .env (local) ou nas variáveis do Railway (produção).\n"
        "Formato: postgresql://usuario:senha@host:5432/nome_banco"
    )

DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

# ---------------------------------------------------------------------------
# Validação de senhas
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estáticos
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = []
frontend_static = BASE_DIR.parent / "frontend" / "static"
if frontend_static.exists():
    STATICFILES_DIRS.append(frontend_static)
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Arquivos de mídia
# ---------------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "core.CustomUser"
LOGIN_URL = "core:login"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ---------------------------------------------------------------------------
# Simple JWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Google Maps
# ---------------------------------------------------------------------------
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
