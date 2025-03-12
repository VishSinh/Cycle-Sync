from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'period_tracking',
        'ENFORCE_SCHEMA': True, 
        'CLIENT': {
            'host': 'mongodb://mongodb:27017/',
        },
        'CONN_MAX_AGE' : None,
    }
}