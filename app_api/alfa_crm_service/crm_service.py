import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import redis
from celery_app import app
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CRM_HOSTNAME = os.getenv("CRM_HOSTNAME")
CRM_EMAIL = os.getenv("CRM_EMAIL")
CRM_API_KEY = os.getenv("CRM_API_KEY")

BASE_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "application/json, text/plain, */*",
}

branches = [1, 2, 3, 4]
client_is_study_statuses = [0, 1]

REQUEST_LIMIT = 2  # Максимальное количество одновременных запросов
MAX_RETRIES = 5  # Максимальное количество попыток
RETRY_DELAY = 2  # Начальная задержка между попытками


def get_redis_client():
    """
    Создает и возвращает клиент Redis.
    """
    return redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

@app.task
def update_crm_token():
    """
    Задача для обновления токена в Redis.
    """
    token = login_to_alfa_crm()
    if token:
        # Сохраняем токен в Redis с TTL 55 минут (3300 секунд)
        redis_client = get_redis_client()
        redis_client.set("crm_token", token, ex=3300)
        logger.info("Токен успешно обновлен и сохранен в Redis.")
    else:
        logger.error("Не удалось обновить токен.")


def get_crm_token():
    """
    Получение токена из Redis или через авторизацию.
    """
    redis_client = get_redis_client()
    token = redis_client.get("crm_token")

    if token:
        logger.info("Токен успешно получен из Redis.")
        return token
    else:
        logger.info("Токен отсутствует в Redis. Запрашиваем новый токен...")
        token = login_to_alfa_crm()
        if token:
            # Сохраняем токен в Redis с TTL 55 минут (3300 секунд)
            redis_client.set("crm_token", token, ex=3300)
            logger.info("Новый токен сохранен в Redis.")
            return token
        else:
            logger.error("Не удалось получить токен.")
            return None


def login_to_alfa_crm():
    """
    Авторизация в CRM и получение токена.
    """
    email = os.getenv("CRM_EMAIL")
    api_key = os.getenv("CRM_API_KEY")
    logger.info(f"Начинается авторизация в CRM с email: {email}...")

    data = {"email": email, "api_key": api_key}
    url = f"https://{CRM_HOSTNAME}/v2api/auth/login"
    logger.debug(f"URL для авторизации: {url}")
    logger.debug(f"Данные для авторизации: {data}")

    try:
        logger.info("Отправка POST-запроса для авторизации...")
        response = requests.post(url, headers=BASE_HEADERS, json=data)
        logger.debug(
            f"Получен ответ от сервера: статус {response.status_code}, тело: {response.text}"
        )

        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("token")
            logger.info(f"Токен успешно получен: {token[:10]}... (первые 10 символов)")
            return token
        else:
            logger.error(f"Ошибка авторизации: статус {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Произошла ошибка при отправке запроса для авторизации: {e}")
        return None


def find_user_by_phone(phone_number: str) -> dict | None:
    """
    Поиск пользователя по номеру телефона.
    """
    logger.info(f"Начинается поиск пользователя по номеру телефона: {phone_number}")

    token = get_crm_token()
    if not token:
        logger.error("Не удалось получить токен для поиска пользователя.")
        return None

    def fetch_data(branch: str, status: int) -> dict | None:
        """
        Выполнение одного запроса к CRM.
        """
        data = {"is_study": status, "page": 0, "phone": phone_number}
        url = f"https://{CRM_HOSTNAME}/v2api/{branch}/customer/index"
        logger.info(
            f"Выполняется запрос для branch={branch}, status={status}, URL: {url}"
        )
        logger.debug(f"Данные для запроса: {data}")

        response = send_request_to_crm(url=url, data=data, params=None, token=token)
        if response:
            logger.info(
                f"Успешный ответ для branch={branch}, status={status}"
            )
        else:
            logger.warning(
                f"Не удалось получить данные для branch={branch}, status={status}"
            )
        return response

    # Собираем все комбинации (branch, status)
    tasks = [
        (str(branch), status)
        for status in client_is_study_statuses
        for branch in branches
    ]
    logger.info(
        f"Сформированы задачи для выполнения: {len(tasks)} комбинаций филиалов и статусов."
    )

    results = []
    with ThreadPoolExecutor(max_workers=REQUEST_LIMIT) as executor:
        logger.info(
            f"Запуск выполнения задач с ограничением {REQUEST_LIMIT} одновременных запросов."
        )
        futures = [
            executor.submit(fetch_data, branch, status) for branch, status in tasks
        ]
        for future in futures:
            result = future.result()
            if result is not None:
                results.append(result)
                # logger.info(f"Добавлен результат: {result}")
            else:
                logger.warning("Получен пустой результат, пропускаем.")

    # Обработка результатов
    total_sum = sum(result.get("total", 0) for result in results)
    count_sum = sum(result.get("count", 0) for result in results)
    all_items = [item for result in results for item in result.get("items", [])]

    result_answer = {
        "total": total_sum,
        "count": count_sum,
        "items": all_items,
    }
    return result_answer


def create_user_in_crm(user_data):
    """
    Создание нового пользователя в CRM.
    """
    logger.info("Начинается процесс создания нового пользователя в CRM.")

    token = get_crm_token()
    if not token:
        logger.error("Не удалось получить токен для создания пользователя.")
        return None

    client_name = (
        f"{user_data['first_name']} {user_data['last_name']} | {user_data['username']}"
    )
    data = {
        "name": client_name,
        "phone": user_data["phone_number"],
        "branch_ids": 1,
        "legal_type": 1,
        "is_study": 0,
        "note": "created by Telegram BOT",
    }
    url = f"https://{CRM_HOSTNAME}/v2api/1/customer/create"

    logger.info(f"Отправка данных для создания пользователя: {data}")
    logger.debug(f"URL для создания пользователя: {url}")

    try:
        response = requests.post(
            url, headers={**BASE_HEADERS, "X-ALFACRM-TOKEN": token}, json=data
        )
        logger.debug(
            f"Получен ответ от сервера: статус {response.status_code}, тело: {response.text}"
        )

        if response.status_code == 200:
            logger.info("Пользователь успешно создан.")
            return response
        else:
            logger.error(
                f"Ошибка создания пользователя: статус {response.status_code}, тело: {response.text}"
            )
            return None
    except Exception as e:
        logger.error(f"Произошла ошибка при создании пользователя: {e}")
        return None


def send_request_to_crm(url: str, data: dict, params: dict | None, token: str | None) -> dict | None:
    if not token:
        logger.error("Токен отсутствует. Отмена запроса.")
        return None

    headers = {**BASE_HEADERS, "X-ALFACRM-TOKEN": token}
    retry_delay = RETRY_DELAY
    logger.info(
        f"Начинается отправка запроса к CRM. URL: {url}, Данные: {data}, Параметры: {params}"
    )

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                f"Попытка {attempt + 1}/{MAX_RETRIES}. Отправка POST-запроса..."
            )
            with ThreadPoolExecutor(max_workers=REQUEST_LIMIT) as executor:
                future = executor.submit(
                    requests.post,
                    url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=10,
                )
                response = future.result()

            logger.debug(
                f"Получен ответ от сервера: статус {response.status_code}, тело: {response.text}"
            )

            if response.status_code == 200:
                logger.info("Запрос успешно выполнен.")
                try:
                    # Пытаемся преобразовать ответ в JSON
                    return response.json()
                except json.JSONDecodeError:
                    logger.error("Ошибка декодирования JSON. Ответ: %s", response.text)
                    return None
            elif response.status_code == 401:
                logger.error("Неавторизованный запрос. Отмена запроса.")
                return None
            elif response.status_code == 429:
                logger.warning(
                    f"Слишком много запросов. Повторная попытка через {retry_delay} секунд..."
                )
                sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                logger.error(
                    f"Неожиданный статус: {response.status_code}. Тело: {response.text}"
                )
                return None
        except requests.RequestException as e:
            logger.error(f"Ошибка при отправке запроса: {e}")
            return None

    logger.error("Достигнуто максимальное количество попыток. Запрос не выполнен.")
    return None


def get_client_lessons(user_crm_id: int, branch_id: int, page: int | None = None, lesson_status: int = 1,
                       lesson_type: int = 2) -> dict | None:
    token = get_crm_token()
    if not token:
        logger.error("Не удалось получить токен для создания пользователя.")
        return None

    data = {
        "customer_id": user_crm_id,
        "status": lesson_status,  # 1 - запланирован урок, 2 - отменен, 3 - проведен
        "lesson_type_id": lesson_type,  # 3 - пробник, 2 - групповой
        "page": 0 if page is None else page,
    }

    url = f"https://{CRM_HOSTNAME}/v2api/{branch_id}/lesson/index"

    response_data = send_request_to_crm(url, data, params=None, token=token)
    if response_data:
        # Проверяем структуру ответа
        if isinstance(response_data, dict) and "total" in response_data:
            logger.info(f"Получено уроков: {response_data.get('total')}")
            return response_data
        else:
            logger.error(f"Некорректный ответ от CRM: {response_data}")
            return {"total": 0}
    else:
        logger.warning(f"Не удалось получить данные уроков")
        return {"total": 0}
