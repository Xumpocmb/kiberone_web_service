import requests
from celery import shared_task
from django.conf import settings

from app_kiberclub.models import Client, AppUser
from django.utils import timezone
import logging
from datetime import date


logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, text):
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не настроен")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            raise Exception(f"Ошибка Telegram API: {response.text}")
    except Exception as e:
        logger.error(e)

    logger.info(f"[Telegram] Отправлено сообщение для {chat_id}: {text}")
    pass


@shared_task
def send_birthday_congratulations():
    """
    Проверяет клиентов и отправляет поздравления с днем рождения
    """
    today = date.today()
    logger.info("Запущена проверка дней рождения клиентов и отправка поздравлений...")

    # Получаем всех клиентов, у которых сегодня день рождения
    clients = Client.objects.select_related("user").filter(
        dob__day=today.day,
        dob__month=today.month
    )

    for client in clients:
        user: AppUser = client.user
        if not user or not user.telegram_id:
            continue

        message = (
            f"🎂 Поздравляем с Днем Рождения, {client.first_name}! 🎉\n\n"
            f"Команда KIBERone желает тебе успехов в учебе, новых открытий и достижений!\n\n"
            f"Пусть этот день будет наполнен радостью и счастьем!\n\n"
            f"Твой KIBERone! ❤️"
        )

        try:
            send_telegram_message(user.telegram_id, message)
            logger.info(f"Поздравление с днем рождения отправлено пользователю {user.telegram_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке поздравления пользователю {user.telegram_id}: {e}")


@shared_task
def check_clients_balance_and_notify():
    """
    Проверяет клиентов и отправляет уведомления тем, у кого paid_lesson_count < 1
    В зависимости от даты отправляет разные сообщения:
    - до 10-го числа: обычное уведомление
    - после 10-го числа: напоминание с ссылкой на оплату
    """
    now = timezone.now()
    logger.info("Запущена проверка баланса клиентов и отправка уведомлений...")

    clients = Client.objects.select_related("user").filter(paid_lesson_count__lt=1)

    for client in clients:
        user: AppUser = client.user
        if not user or not user.telegram_id:
            continue

        message = (
            f"🔔 Это PUSH уведомление о необходимости пополнить KIBERказну\n\n"
            "Чтобы оплатить обучение KIBERone, нажмите на боковую кнопку Меню->КИБЕРменю->Оплатить\n\n"
            "Ваш KIBERone!\n"
        )
        
        reminder_message = (
            "Уважаемый клиент!\n"
            "У нас не отобразилась ваша оплата за занятия.\n"
            "Чтобы оплатить обучение KIBERone, нажмите на боковую кнопку Меню->КИБЕРменю->Оплатить\n\n"
            "Ваш KIBERone!\n")

        # Выбираем сообщение в зависимости от текущей даты
        current_day = now.day
        notification_text = message if current_day <= 10 else reminder_message

        try:
            send_telegram_message(user.telegram_id, notification_text)
            logger.info(f"Уведомление отправлено пользователю {user.telegram_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user.telegram_id}: {e}")
