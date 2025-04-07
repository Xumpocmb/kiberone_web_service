#!/bin/bash
# Запуск Celery Worker
celery -A celery_app worker --loglevel=info &

# Запуск Celery Beat
celery -A celery_app beat --loglevel=info &
