from email import message
import requests
from celery import shared_task
from django.conf import settings

from app_kiberclub.models import Client, AppUser, Location
from django.utils import timezone
import logging
import datetime
from datetime import date
from app_api.alfa_crm_service.crm_service import get_client_lessons


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
            f"🎂 Поздравляем с Днем Рождения, {client.name}! 🎉\n\n"
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
        
        lesson_response = get_client_lessons(user_crm_id=client.crm_id, branch_id=client.branch_id, lesson_status=1, lesson_type=2)
        if lesson_response.get('total', 0) > lesson_response.get('count', 0):
            page = lesson_response.get('total', 0) // lesson_response.get('count', 1)
        else:
            page = 0
        lesson_response = get_client_lessons(user_crm_id=client.crm_id, branch_id=client.branch_id, lesson_status=1, lesson_type=2, page=page)
        last_user_lesson = lesson_response.get("items", [])[-1]
        next_lesson_date = last_user_lesson.get("lesson_date") if last_user_lesson.get("lesson_date") else last_user_lesson.get("date")
        
        # если урок сегодня, то отправить уведомление
        if timezone.now().strftime("%Y-%m-%d") == next_lesson_date:
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
                continue


@shared_task
def check_clients_lessons_before():
    """
    Проверяет клиентов и отправляет уведомления тем, у кого пробные занятия завтра
    """
    
    # Получаем клиентов с количеством оплаченных занятий меньше 1
    clients = Client.objects.select_related("user").filter(paid_lesson_count__lt=1)

    for client in clients:
        
        # Запрос пробных занятий
        lesson_response = get_client_lessons(user_crm_id=client.crm_id, branch_id=client.branch_id, lesson_status=1, lesson_type=3)
        
        total_trial_lessons = lesson_response.get("total", 0)
        
        if total_trial_lessons > 0:
            trial_lesson = lesson_response.get("items", [])[0]
            lesson_date = trial_lesson.get("date", None)
            lesson_time = f"{trial_lesson.get('time_from').split(' ')[1][:-3]}"
            room_id = trial_lesson.get("room_id", None)
            
            
            # Поиск локации
            location = Location.objects.filter(location_crm_id=room_id).first()
            
            if location:
                message = (
                    f"🔔 Ваше пробное занятие в КИБЕР-школе уже завтра!\n"
                    f"Дата: {lesson_date.split('-')[2]}.{lesson_date.split('-')[1]}\n"
                    f"Время: {lesson_time}\n"
                    f"Адрес: {location.name}\n{location.map_url}\n\n"
                    "Ваш KIBERone ♥"
                )
                try:
                    send_telegram_message(client.user.telegram_id, message)
                except Exception as e:
                    continue
        
        # НАПОМИНАНИЕ О ПЕРВОМ ЗАНЯТИИ
        
        # запланированные уроки
        lesson_response = get_client_lessons(user_crm_id=client.crm_id, branch_id=client.branch_id, lesson_status=1, lesson_type=2)
        
        planned_lessons_count = lesson_response.get("total", 0)
        
        if planned_lessons_count > 0:
            # проведенные уроки
            user_taught_lessons = get_client_lessons(user_crm_id=client.crm_id, branch_id=client.branch_id, lesson_status=3, lesson_type=2)
            # если нет посещенных уроков
            taught_lessons_count = user_taught_lessons.get("total", 0)
            
            if taught_lessons_count == 0:
                # забираем последний запланированный урок
                if lesson_response.get('total', 0) > lesson_response.get('count', 0):
                    page = lesson_response.get('total', 0) // lesson_response.get('count', 1)
                else:
                    page = 0
                lesson_response = get_client_lessons(user_crm_id=client.crm_id, branch_id=client.branch_id, lesson_status=1, lesson_type=2, page=page)
                
                last_user_lesson = lesson_response.get("items", [])[-1]
                
                next_lesson_date = last_user_lesson.get("lesson_date") if last_user_lesson.get("lesson_date") else last_user_lesson.get("date")
                
                room_id = last_user_lesson.get("room_id", None)
                location = Location.objects.filter(location_crm_id=room_id).first()
                
                
                # проверить что урок завтра
                tomorrow_date = (timezone.now() + timezone.timedelta(days=1)).strftime("%Y-%m-%d")
                
                if next_lesson_date == tomorrow_date:
                    message = (
                        f"🔔 Ваше первое занятие в КИБЕР-школе уже завтра!\n"
                        f"Дата: {next_lesson_date.split('-')[2]}.{next_lesson_date.split('-')[1]}\n"
                        f"Время: {last_user_lesson.get('time_from').split(' ')[1][:-3]}\n"
                        f"Адрес: {location.name}\n{location.map_url}\n\n"
                        "Ваш KIBERone ♥"
                    )
                    
                    try:
                        send_telegram_message(client.user.telegram_id, message)
                    except Exception as e:
                        continue
