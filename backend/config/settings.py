"""Configuración de SiCMI.

Lo que cambia entre equipos (clave secreta, modo de depuración, hosts, base de datos)
se lee de variables de entorno o del archivo backend/.env. Nada secreto va en el código.
"""
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _cargar_env(ruta):
    """Lee un archivo .env sencillo (CLAVE=valor) sin instalar librerías."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding='utf-8-sig').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#') or '=' not in linea:
            continue
        clave, valor = linea.split('=', 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env(BASE_DIR / '.env')


def env(nombre, defecto=''):
    return os.environ.get(nombre, defecto)


def env_bool(nombre, defecto=False):
    return env(nombre, str(defecto)).strip().lower() in ('1', 'true', 'si', 'sí', 'yes')


def env_lista(nombre, defecto=''):
    return [x.strip() for x in env(nombre, defecto).split(',') if x.strip()]


# ---------------------------------------------------------------- seguridad básica
DEBUG = env_bool('DJANGO_DEBUG', False)

SECRET_KEY = env('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'clave-solo-para-desarrollo-no-usar-en-produccion'
    else:
        raise ImproperlyConfigured(
            'Falta DJANGO_SECRET_KEY. Defínala en backend/.env (vea .env.example).')

ALLOWED_HOSTS = env_lista('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]' if DEBUG else '')
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('Falta DJANGO_ALLOWED_HOSTS (el nombre con el que se accede al servidor).')

X_FRAME_OPTIONS = 'DENY'

# Si el sitio se sirve por HTTPS (detrás de Nginx u otro proxy)
if env_bool('DJANGO_HTTPS', False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = int(env('DJANGO_HSTS_SEGUNDOS', '3600'))  # súbalo cuando todo funcione bien
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SSL_REDIRECT', False)

CSRF_TRUSTED_ORIGINS = env_lista('CSRF_TRUSTED_ORIGINS')

# ---------------------------------------------------------------- aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'corsheaders',
    # SiCMI
    'accounts',
    'catalogos',
    'solicitudes',
    'recursos',
    'personal',
    'transporte',
    'ordenes',
    'anexos',
    'plan',
    'reportes',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------- datos (fuera del proyecto)
# La base de datos, las fotos, los croquis y los registros viven FUERA del código:
# sobreviven a actualizar, reemplazar o volver a clonar el proyecto.
DATOS_DIR = Path(env('SICMI_DATOS', str(Path.home() / 'SiCMI-datos')))
DATOS_DIR.mkdir(parents=True, exist_ok=True)

if env('DB_ENGINE', 'sqlite').strip().lower() in ('postgres', 'postgresql'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', 'sicmi'),
            'USER': env('DB_USER', 'sicmi'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST', 'localhost'),
            'PORT': env('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DATOS_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------- idioma y archivos
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Havana'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = DATOS_DIR / 'static'          # collectstatic copia aquí los estilos del admin
MEDIA_URL = '/media/'
MEDIA_ROOT = DATOS_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------- API
CORS_ALLOWED_ORIGINS = env_lista('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    # En producción la API responde solo JSON (sin la interfaz de pruebas del navegador)
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'] + (
        ['rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG else []),
    # Límite de intentos de inicio de sesión (contra adivinación de contraseñas)
    'DEFAULT_THROTTLE_RATES': {'login': env('SICMI_LOGIN_RATE', '10/min')},
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=int(env('SICMI_SESION_HORAS', '8'))),
}

# ---------------------------------------------------------------- registros (logs)
LOG_DIR = DATOS_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'normal': {'format': '{asctime} {levelname} {name} {message}', 'style': '{'}},
    'handlers': {
        'consola': {'class': 'logging.StreamHandler', 'formatter': 'normal'},
        'archivo': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'sicmi.log'),
            'maxBytes': 2_000_000,
            'backupCount': 5,
            'encoding': 'utf-8',
            'formatter': 'normal',
        },
    },
    'root': {'handlers': ['consola', 'archivo'], 'level': 'WARNING'},
    'loggers': {
        # Solo los errores 500 van al archivo (los 404 y 403 normales no ensucian el registro)
        'django.request': {'handlers': ['consola', 'archivo'], 'level': 'ERROR', 'propagate': False},
    },
}