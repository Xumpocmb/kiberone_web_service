from django.contrib import admin
from app_kiberclub.models import AppUser, Client, Branch, QuestionsAnswers


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
