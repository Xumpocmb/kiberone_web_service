from celery import Celery
from django.conf import settings
import os

from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_web_service.settings")

app = Celery("_web_service")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Используем планировщик из базы данных
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
