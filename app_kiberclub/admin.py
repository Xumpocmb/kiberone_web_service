import logging
from time import sleep

import requests
from django.conf import settings
from django.contrib import admin, messages

from app_kiberclub.models import (
    AppUser,
    Client,
    Branch,
    QuestionsAnswers,
    EripPaymentHelp,
    PartnerCategory,
    PartnerClientBonus,
    ClientBonus,
    SalesManager,
    SocialLink,
    Location,
    Manager, BroadcastMessage,
)

logger = logging.getLogger(__name__)


class ClientInline(admin.TabularInline):
    """
    Inline для редактирования клиентов на странице пользователя.
    """

    model = Client
    extra = 1  # Количество пустых форм для добавления новых клиентов
    fields = [
        "branch",
        "name",
        "crm_id",
        "is_study",
        "has_scheduled_lessons",
    ]  # Поля для отображения
    readonly_fields = ["crm_id"]  # Если crm_id не должен редактироваться


@admin.register(AppUser)
class BotUserAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели BotUser.
    """

    list_display = ["phone_number", "telegram_id", "username", "client_count"]
    search_fields = ["telegram_id", "phone_number"]
    inlines = [ClientInline]  # Добавляем inline для клиентов

    def client_count(self, obj):
        """
        Отображает количество клиентов у пользователя.
        """
        return obj.clients.count()

    client_count.short_description = "Количество детей"


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели Client.
    """

    list_display = ["user", "branch", "crm_id", "is_study"]
    list_filter = ["is_study", "branch"]
    search_fields = ["crm_id", "user__username", "user__telegram_id"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели Branch.
    """

    list_display = ["name"]
    search_fields = ["name"]


@admin.register(QuestionsAnswers)
class QuestionsAnswersAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели QuestionsAnswers.
    """

    list_display = ["question", "answer"]
    search_fields = ["question", "answer"]

    class Meta:
        verbose_name = "Вопрос-Ответ"
        verbose_name_plural = "Вопросы-Ответы"


@admin.register(EripPaymentHelp)
class EripPaymentHelpAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели EripPaymentHelp.
    """

    list_display = ["erip_link", "erip_instructions"]
    search_fields = ["erip_link", "erip_instructions"]


@admin.register(PartnerCategory)
class PartnerCategoryAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели PartnerCategory.
    """

    list_display = ["name"]

@admin.register(PartnerClientBonus)
class PartnerClientBonusAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели PartnerClientBonus.
    """

    list_display = ["partner_name", "category"]
    search_fields = ["partner_name"]


@admin.register(ClientBonus)
class ClientBonusAdmin(admin.ModelAdmin):
    """
    Админ-класс для модели ClientBonus.
    """

    list_display = ["bonus"]


@admin.register(SalesManager)
class SalesManagerAdmin(admin.ModelAdmin):
    list_display = ("name", "telegram_link", "get_branches")
    filter_horizontal = ("branches",)

    def get_branches(self, obj):
        return ", ".join([branch.name for branch in obj.branches.all()])

    get_branches.short_description = "Филиалы"


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "link")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("branch", "name", "location_crm_id")
    list_filter = ["branch"]


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ("name", "telegram_link")



@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'status_filter')

    def save_model(self, request, obj, form, change):
        obj.sent_by = request.user
        super().save_model(request, obj, form, change)

        users = AppUser.objects.exclude(telegram_id__isnull=True).exclude(telegram_id__exact='')

        if obj.status_filter:
            users = users.filter(status=obj.status_filter)

        success = 0
        fail = 0

        for user in users:
            if send_telegram_message(
                    chat_id=user.telegram_id,
                    text=obj.message_text,
                    image_path=obj.image.path if obj.image else None
            ):
                success += 1
            else:
                fail += 1
            sleep(0.2)

        if success > 0:
            messages.success(request, f"Успешно отправлено: {success} сообщений")
        if fail > 0:
            messages.warning(request, f"Не удалось отправить: {fail} сообщений")


def send_telegram_message(chat_id, text, image_path=None):
    """
    Отправка сообщения через Telegram Bot API
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в settings.py")
        return False

    base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"

    try:
        if image_path:
            url = base_url + "sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': chat_id, 'caption': text}
                response = requests.post(url, files=files, data=data)
        else:
            url = base_url + "sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data)

        if response.status_code != 200:
            logger.error(f"Ошибка Telegram API: {response.status_code} - {response.text}")
            return False

        return True

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {str(e)}")
        return False