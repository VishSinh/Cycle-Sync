import os
from pathlib import Path
from os import getenv as os_getenv
from datetime import timedelta

from utils.logger import get_django_logging_config


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

#################################################################
##################### ENVIRONMENT VARIABLES #####################
#################################################################
SECRET_KEY = os_getenv('SECRET_KEY')
DEBUG = os_getenv('DEBUG') == 'True'
ALLOWED_HOSTS = os_getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,0.0.0.0').split(',')
MONGO_DB_URI = os_getenv('MONGO_DB_URI', 'mongodb://mongodb:27017/')
# APPLICATION SETTINGS
SESSION_SECRET_KEY = os_getenv('SESSION_SECRET_KEY')
SESSION_EXPIRY = int(os_getenv('SESSION_EXPIRY', '3600'))
USER_ID_HASH_SALT = os_getenv('USER_ID_HASH_SALT')

# CELERY SETTINGS
CELERY_BROKER_URL = os_getenv('CELERY_BROKER_URL')

# RATE LIMIT SETTINGS
# NON_REGISTERED_RATE_LIMIT = int(os_getenv('NON_REGISTERED_RATE_LIMIT'))  
# REGISTERED_RATE_LIMIT = int(os_getenv('REGISTERED_RATE_LIMIT'))  
# RATE_LIMIT_WINDOW = timedelta(hours=int(os_getenv('RATE_LIMIT_WINDOW')))

GEMINI_API_KEY = os_getenv('GEMINI_API_KEY')


#################################################################
##################### DATABASE CONFIGURATION ####################
#################################################################
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'period_tracking',
        'ENFORCE_SCHEMA': True, 
        'CLIENT': {
            'host': MONGO_DB_URI,
        },
        'CONN_MAX_AGE' : None,
    }
}

#################################################################
##################### INSTALLED APPLICATIONS ####################
#################################################################
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

#################################################################
########################## MIDDLEWARE ###########################
#################################################################
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add CORS middleware before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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

#################################################################
####################### CORS CONFIGURATION ######################
#################################################################
CORS_ALLOW_ALL_ORIGINS = False  # Set to True to allow all origins (not recommended for production)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  
    "http://127.0.0.1:3000",
    "https://cycle-sync-webapp.vercel.app",
    "http://localhost:8000", 
    "http://127.0.0.1:8000", 
    "http://0.0.0.0:8000",    
]
# https://cycle-sync-webapp.vercel.app/auth

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
    'referer',
]

# CSP_CONNECT_SRC = ("'self'", "http://127.0.0.1:3000", "http://127.0.0.1:8000")

# Set to True if you want to allow cookies to be included in cross-site requests
CORS_ALLOW_CREDENTIALS = True


# CSRF_TRUSTED_ORIGINS = [
#     "http://localhost:3000",
#     # "https://your-next-app.com",
# ]

# ACCESS_CONTROL_ALLOW_ORIGIN = [
#     "http://localhost:3000",
#     # "https://your-next-app.com",
# ]


# # Add this setting for older django-cors-headers versions
# CORS_REPLACE_HTTPS_REFERER = True

# # Make sure these settings are included for proper CORS handling
# CORS_URLS_REGEX = r'^/api/.*$'
# CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

#################################################################
###################### URL CONFIGURATION #######################
#################################################################
ROOT_URLCONF = 'period_tracking_BE.urls'

#################################################################
################### TEMPLATE CONFIGURATION #####################
#################################################################
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

#################################################################
################## AUTHENTICATION CONFIGURATION #################
#################################################################
# Password validation
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

#################################################################
####################### LOGGING CONFIGURATION ###################
#################################################################
LOG_DIR = os.path.join(BASE_DIR, 'logs')
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

#################################################################
####################### INTERNATIONALIZATION ###################
#################################################################
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

#################################################################
####################### STATIC FILES ###########################
#################################################################
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

#################################################################
####################### MISCELLANEOUS ##########################
#################################################################
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




