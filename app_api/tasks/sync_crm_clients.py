from celery import shared_task
from app_api.services.crm_sync import sync_all_users_with_crm
import logging

logger = logging.getLogger(__name__)

@shared_task
def sync_all_clients_task():
    logger.info("Запуск ежедневной синхронизации клиентов из CRM")
    try:
        sync_all_users_with_crm()
        logger.info("✅ Синхронизация клиентов завершена успешно")
    except Exception as e:
        logger.exception(f"❌ Ошибка при синхронизации: {e}")
