"""
Configuração do servidor Django da Plataforma Inteligente de Imóveis.

Os valores sensíveis e os que mudam entre ambientes (base de dados, chave
secreta, modo de depuração) são lidos de variáveis de ambiente. Assim o mesmo
código corre no computador de desenvolvimento e no Docker.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "chave-apenas-para-desenvolvimento-nao-usar-em-producao"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Bibliotecas externas
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
    # Aplicações do projecto (uma por módulo da arquitectura)
    "contas",          # Autenticação e Perfis
    "anuncios",        # Gestão de Anúncios, Pesquisa e Filtros
    "ia",              # Módulos de Inteligência Artificial
    "administracao",   # Painel de Administração, alertas, parâmetros e logs
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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

# Base de dados: PostgreSQL no Docker; SQLite quando não há variáveis definidas
# (útil para correr os testes rapidamente no computador de cada membro).
if os.environ.get("DATABASE_URL"):
    # Alojamento (Render): a base de dados vem num único endereço postgres://...
    from urllib.parse import urlparse
    _url = urlparse(os.environ["DATABASE_URL"])
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _url.path.lstrip("/"),
            "USER": _url.username,
            "PASSWORD": _url.password,
            "HOST": _url.hostname,
            "PORT": _url.port or 5432,
            "CONN_MAX_AGE": 60,
        }
    }
elif os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ.get("POSTGRES_USER", "imoveis"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "imoveis"),
            "HOST": os.environ.get("POSTGRES_HOST", "db"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Modelo de utilizador próprio (ver contas/models.py)
AUTH_USER_MODEL = "contas.Utilizador"

# Regras da palavra-passe (validação no servidor, UC14 e UC17)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Língua e fuso horário de Moçambique
LANGUAGE_CODE = "pt"
TIME_ZONE = "Africa/Maputo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))
# Alojamento num só serviço: o WhiteNoise serve os ficheiros estáticos e, se
# FRONTEND_DIST estiver definido, o cliente React compilado (ver config/urls.py)
FRONTEND_DIST = os.environ.get("FRONTEND_DIST")
if FRONTEND_DIST:
    WHITENOISE_ROOT = FRONTEND_DIST

# Atrás do proxy HTTPS do alojamento
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").split(",") if h
]

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework: servidor sem estado, autenticação por token (RNF04)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "config.paginacao.Paginacao",
    "PAGE_SIZE": 12,
    # Limite de pedidos ao assistente e ao serviço de mapas (RNF09)
    "DEFAULT_THROTTLE_RATES": {"assistente": "30/min", "mapa": "60/min"},
}

# O cliente React corre noutro endereço durante o desenvolvimento
CORS_ALLOW_ALL_ORIGINS = True

# Tamanho máximo de cada fotografia (5 MB) e número máximo por anúncio
TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024
MAXIMO_IMAGENS_POR_ANUNCIO = 8
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
