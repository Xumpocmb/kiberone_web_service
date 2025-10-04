import logging
from app_kiberclub.models import Client

logger = logging.getLogger(__name__)


def update_bot_user_status(user):
    """
    Обновляет статус пользователя на основе статусов его клиентов.
    ---
    Алгоритм:
    1. Если у пользователя есть хотя бы один клиент с is_study=True,
       устанавливаем статус пользователя в "2" (Клиент).
    2. Иначе, если у пользователя есть хотя бы один клиент с has_scheduled_lessons=True,
       устанавливаем статус пользователя в "1" (Lead с группой).
    3. Иначе, устанавливаем статус пользователя в "0" (Lead).
    """
    # Проверяем, есть ли хотя бы один клиент с is_study=True
    has_active_clients = Client.objects.filter(user=user, is_study=True).exists()

    # Если нет активных клиентов, проверяем наличие запланированных уроков
    if not has_active_clients:
        has_scheduled_lessons = Client.objects.filter(
            user=user, has_scheduled_lessons=True
        ).exists()
        user.status = "1" if has_scheduled_lessons else "0"
    else:
        user.status = "2"  # Клиент

    user.save()
    logger.info(f"Статус пользователя {user.id} обновлен: {user.status}")