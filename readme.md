sudo systemctl start redis
redis-server
celery -A celery_app worker --loglevel=info

source venv/bin/activate


запуск теста на поиск пользователя:
python manage.py test app_crm_api.tests.CrmApiTests.test_find_user


admin:
kiberadmin
kiberone1221