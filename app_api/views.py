from django.shortcuts import render
import logging
from rest_framework.decorators import api_view
from app_api.alfa_crm_service.crm_service import find_user_by_phone, create_user_in_crm
from rest_framework import status
from rest_framework.response import Response

from app_kiberclub.models import AppUser

logger = logging.getLogger(__name__)


@api_view(["POST"])
def find_user_by_phone_view(request) -> Response:
    phone_number = request.data.get("phone_number")
    if not phone_number:
        return Response(
            {"success": False, "message": "Номер телефона обязателен"}, status=status.HTTP_400_BAD_REQUEST)
    search_result = find_user_by_phone(phone_number)
    if search_result.get("total", 0) > 0:
        return Response(
            {
                "success": True,
                "message": "Пользователь найден в CRM",
                "user": search_result}, status=status.HTTP_200_OK
        )
    else:
        return Response(
            {
                "success": False,
                "message": "Пользователь не найден в CRM",
                "user": None}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
def register_user_in_crm_view(request) -> Response:
    """
    Регистрация нового пользователя в CRM.
    """
    user_data = request.data
    required_fields = ["first_name", "last_name", "username", "phone_number"]
    if not all(field in user_data for field in required_fields):
        logger.error("Не все обязательные поля указаны")
        return Response(
            {
                "success": False,
                "message": "Не все обязательные поля указаны"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result: dict = create_user_in_crm(user_data)

    if result:
        logger.info("Пользователь успешно зарегистрирован в CRM")
        return Response(
            {"success": True,
             "message": "Пользователь успешно зарегистрирован в CRM",
             "data": result}, status=status.HTTP_201_CREATED
        )
    else:
        logger.error("Ошибка при регистрации в CRM")
        return Response(
            {
                "success": False,
                "message": "Ошибка при регистрации в CRM"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ------------------- DB --------------------
@api_view(["POST"])
def find_user_in_db_view(request) -> Response:
    telegram_id = request.data.get("telegram_id")
    if not telegram_id:
        return Response(
            {
                "success": False,
                "message": "telegram_id обязателен"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = AppUser.objects.filter(telegram_id=telegram_id).first()
        if user:
            return Response(
                {
                    "success": True,
                    "message": "Пользователь найден в базе данных",
                    "user": {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "phone_number": user.phone_number,
                        "status": user.status,
                    },
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response({"success": False}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"message": f"Ошибка при поиске пользователя: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def register_user_in_db_view(request) -> Response:
    """
    Регистрация нового пользователя в базе данных Django.
    """

    try:
        telegram_id = request.data.get("telegram_id")
        username = request.data.get("username")
        phone_number = request.data.get("phone_number")

        if not all([telegram_id, username, phone_number]):
            return Response(
                {
                    "success": False,
                    "message": "Необходимо указать telegram_id, username и phone_number"},
                    status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = AppUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username,
                "phone_number": phone_number,
            },
        )

        if created:
            return Response(
                {
                    "success": True,
                    "message": "Пользователь успешно зарегистрирован в базе данных",
                    "user": {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "phone_number": user.phone_number,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "success": False,
                    "message": "Пользователь уже зарегистрирован в базе данных",
                }, status=status.HTTP_200_OK,
            )
    except Exception as e:
        return Response(
            {
                "success": False,
                "message": f"Ошибка на сервере при регистрации пользователя: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def create_or_update_clients_view(request) -> Response:
    """
    Создает, обновляет или удаляет клиентов в базе данных.
    """
    try:
        # Извлекаем данные из запроса
        user_id = request.data.get("user_id")
        crm_items = request.data.get("crm_items", [])
        print(crm_items)

        if not user_id or not isinstance(crm_items, list):
            logger.error("Отсутствуют обязательные поля: user_id или crm_items")
            return Response(
                {"error": "Необходимо указать user_id и список crm_items"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Получаем пользователя по user_id
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            logger.error(f"Пользователь с user_id={user_id} не найден")
            return Response(
                {"error": "Пользователь с указанным user_id не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Извлекаем все crm_id из CRM
        crm_ids = {str(item["id"]) for item in crm_items}

        # Находим всех клиентов пользователя в базе данных
        existing_clients = Client.objects.filter(user=user)
        existing_crm_ids = {client.crm_id for client in existing_clients}

        # Определяем, какие клиенты нужно удалить
        crm_ids_to_delete = existing_crm_ids - crm_ids

        # Удаляем "лишних" клиентов
        deleted_count = 0
        if crm_ids_to_delete:
            deleted_count = Client.objects.filter(
                crm_id__in=crm_ids_to_delete
            ).delete()[0]
            logger.info(f"Удалено клиентов: {deleted_count}")

        # Создаем или обновляем оставшихся клиентов
        created_count = 0
        updated_count = 0
        for item in crm_items:
            try:
                branch = Branch.objects.get(branch_id=item["branch_ids"][0])
            except Branch.DoesNotExist:
                logger.error(f"Филиал с branch_id={item['branch_ids'][0]} не найден")
                continue

            # Проверяем наличие запланированных уроков
            lessons = get_client_lessons(
                user_crm_id=str(item["id"]),
                branch_id=item["branch_ids"][0],
                lesson_status=1,  # Запланированные уроки
                lesson_type=2,  # Групповые уроки
            )
            has_scheduled_lessons = bool(lessons and lessons.get("total", 0) > 0)

            client, created = Client.objects.update_or_create(
                crm_id=str(item["id"]),
                defaults={
                    "user": user,
                    "branch": branch,
                    "is_study": bool(item["is_study"]),
                    "name": item.get("name"),
                    "dob": parse_date(item.get("dob")),
                    "balance": item.get("balance"),
                    "paid_count": item.get("paid_count"),
                    "next_lesson_date": parse_date(item.get("next_lesson_date")),
                    "paid_till": parse_date(item.get("paid_till")),
                    "note": item.get("note"),
                    "paid_lesson_count": item.get("paid_lesson_count"),
                    "has_scheduled_lessons": has_scheduled_lessons,  # Обновляем поле
                },
            )
            if created:
                created_count += 1
                logger.info(f"Клиент успешно создан: crm_id={item['id']}")
            else:
                updated_count += 1
                logger.info(f"Клиент успешно обновлен: crm_id={item['id']}")

        # Обновляем статус пользователя
        update_bot_user_status(user)

        return Response(
            {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "deleted": deleted_count,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Внутренняя ошибка сервера: {str(e)}")
        return Response(
            {"error": f"Внутренняя ошибка сервера: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )