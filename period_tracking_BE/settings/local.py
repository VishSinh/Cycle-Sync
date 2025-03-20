from .base import *

DEBUG = True

allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost,0.0.0.0')
ALLOWED_HOSTS = allowed_hosts_env.split(',')

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