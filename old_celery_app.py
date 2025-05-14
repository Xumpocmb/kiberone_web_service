from celery import Celery
from django.conf import settings
import os
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_web_service.settings")

app = Celery(
    "_web_service",  # Имя приложения
    broker="redis://localhost:6379/0",  # Redis как брокер
    backend="redis://localhost:6379/0",  # Redis как хранилище результатов
)


# Настройка Celery через Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматическое обнаружение задач в приложениях Django
app.autodiscover_tasks()

# Настройки Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Периодические задачи
app.conf.beat_schedule = {
    "update-crm-token-every-hour": {
        "task": "app_api.services.alfa_crm_service.update_crm_token",
        "schedule": 3300.0,  # Каждые 55 минут
    },
}


app.conf.beat_schedule.update({
    "daily-sync-crm-clients": {
        "task": "app_api.tasks.sync_crm_clients.sync_all_clients_task",
        "schedule": crontab(hour=2, minute=0),  # Каждый день в 2:00 ночи
    },
})
