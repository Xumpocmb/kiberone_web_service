from django.contrib import admin
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
    Manager,
)


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
    list_display = ("name", "telegram_link", "get_branches")  # Отображение филиалов
    filter_horizontal = ("branches",)  # Удобный виджет для управления филиалами

    def get_branches(self, obj):
        return ", ".join([branch.name for branch in obj.branches.all()])

    get_branches.short_description = "Филиалы"


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "link")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "branch")
    list_filter = ["branch"]


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ("name", "telegram_link")
    filter_horizontal = ("locations",)
