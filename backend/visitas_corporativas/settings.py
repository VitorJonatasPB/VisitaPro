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
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-4tse_b7fs7lzkl4uq2vjj1qhucu^91qkmb$^k+$_a89h$^%0tq"
)
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8081",
    "https://*.ngrok-free.app",
    "https://visitapro-production.up.railway.app",
    "https://*.loca.lt",
]

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

ROOT_URLCONF = "visitas_corporativas.urls"

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

WSGI_APPLICATION = "visitas_corporativas.wsgi.application"

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
