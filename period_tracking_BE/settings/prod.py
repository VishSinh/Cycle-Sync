from .base import *

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