import os
from pathlib import Path
from os import getenv as os_getenv
from dotenv import load_dotenv
from datetime import timedelta

from utils.logger import get_django_logging_config

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os_getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# allowed hosts
# ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # Add CORS headers app
    'authentication',
    'cycles',
    'users',
    'predictions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Add CORS middleware before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware'
    # 'period_tracking_BE.middlewares.RateLimitMiddleware',
    'period_tracking_BE.middlewares.auth_middleware.AuthMiddleware',
    'period_tracking_BE.middlewares.exception_middleware.ExceptionMiddleware',
    # 'period_tracking_BE.middlewares.ResponseMiddleware',
]

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False  # Set to True to allow all origins (not recommended for production)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default port
    "http://localhost:8000",  # Django default port
    # Add other origins as needed
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Set to True if you want to allow cookies to be included in cross-site requests
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'period_tracking_BE.urls'

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

WSGI_APPLICATION = 'period_tracking_BE.wsgi.application'

# In settings.py
AUTHENTICATION_BACKENDS = [
    'period_tracking_BE.middlewares.auth_middleware.JWTAuthentication',
    'django.contrib.auth.backends.ModelBackend',  # Keep default backend
]


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'djongo',
#         'NAME': 'period_tracking',
#         'ENFORCE_SCHEMA': True, 
#         'CLIENT': {
#             'host': 'mongodb://mongodb:27017/',
#         },
#         'CONN_MAX_AGE' : None,
#     }
# }

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
#         'LOCATION': 'rate_limit',
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOG_DIR = os.path.join(BASE_DIR, '../logs')

LOGGING = get_django_logging_config(
    log_dir=LOG_DIR,
    console_level='INFO',  # Change to 'DEBUG' in development
    file_level='DEBUG',
    max_file_size_mb=10,
    backup_count=5,
    output_mode='console',  # 'console', 'file', or 'both'
    colored_console=True    # Set to False if you don't want colored output
)
# REST_FRAMEWORK = {
#     # # ... other settings ...
#     # 'DEFAULT_RENDERER_CLASSES': [
#     #     'period_tracking_BE.middlewares.CustomFlexibleRenderer',
#     #     'rest_framework.renderers.BrowsableAPIRenderer',
#     # ],
#     'EXCEPTION_HANDLER': None,
# }


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

#################################################################
##################### ALLOWED ENDPOINTS #########################
#################################################################
SKIP_AUTH_PATTERNS = [
    '/api/v1/auth/',
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#################################################################
##################### ENVIRONMENT VARIABLES #####################
#################################################################
# APPLICATION SETTINGS
SESSION_SECRET_KEY = os_getenv('SESSION_SECRET_KEY')
SESSION_EXPIRY = int(os_getenv('SESSION_EXPIRY'))
USER_ID_HASH_SALT = os_getenv('USER_ID_HASH_SALT')

# CELERY SETTINGS
CELERY_BROKER_URL = os_getenv('CELERY_BROKER_URL')

# RATE LIMIT SETTINGS
NON_REGISTERED_RATE_LIMIT = int(os_getenv('NON_REGISTERED_RATE_LIMIT'))  
REGISTERED_RATE_LIMIT = int(os_getenv('REGISTERED_RATE_LIMIT'))  
RATE_LIMIT_WINDOW = timedelta(hours=int(os_getenv('RATE_LIMIT_WINDOW')))

GEMINI_API_KEY = os_getenv('GEMINI_API_KEY')

