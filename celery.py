from __future__ import absolute_import, unicode_literals
from os import environ as os_environ
from celery import Celery
from django.conf import settings
from celery.schedules import crontab
from datetime import timedelta

os_environ.setdefault('DJANGO_SETTINGS_MODULE', 'period_tracking_BE.settings')

app = Celery('period_tracking_BE')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


app.conf.beat_schedule = {
    
    # Is used to update the period records if end_datetime is not set for more than 7 days
    'update_period_records': {
        'task': 'cycles.tasks.update_period_records',
        'schedule': timedelta(hours=24),  
    },
}
