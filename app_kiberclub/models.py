from django.db import models

class Branch(models.Model):
    """
    Модель филиала.
    """
    branch_id = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="ID филиала в ЦРМ")
    name = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Название филиала")
    sheet_url = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Ссылка на таблицу")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "branch"
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"


class Location(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    name = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Название Локации")
    sheet_name = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Название листа в таблице")
    map_url = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ссылка на карту")

    def __str__(self):
        return f"{self.name} (Филиал: {self.branch.name})"

    class Meta:
        db_table = "locations"
        verbose_name = "Локация"
        verbose_name_plural = "Локации"


class AppUser(models.Model):
    """
    Модель пользователя (родителя).
    """
    CLIENT_STATUS = (
        ("0", "Lead"),
        ("1", "Lead with group"),
        ("2", "Client"),
    )

    status = models.CharField(
        choices=CLIENT_STATUS, default="0", max_length=5, verbose_name="Статус клиента"
    )

    telegram_id = models.CharField(
        max_length=100, unique=True, blank=True, null=True, verbose_name="Телеграм ID"
    )
    username = models.CharField(
        max_length=100, unique=False, blank=True, null=True, verbose_name="Username"
    )
    phone_number = models.CharField(
        max_length=100,
        unique=False,
        blank=True,
        null=True,
        verbose_name="Номер телефона",
    )

    def __str__(self):
        return f"{self.username or 'Пользователь'} (ID: {self.telegram_id})"

    class Meta:
        db_table = "bot_users"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Client(models.Model):
    """
    Модель клиента (ребенка).
    """

    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="clients",
        verbose_name="Пользователь",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Имя")
    branch = models.ForeignKey(
        "Branch", on_delete=models.CASCADE, verbose_name="Филиал"
    )
    crm_id = models.CharField(
        max_length=100, unique=True, blank=True, null=True, verbose_name="ID в CRM"
    )

    is_study = models.BooleanField(default=False, verbose_name="Является клиентом")
    dob = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Баланс"
    )
    paid_count = models.IntegerField(
        blank=True, null=True, verbose_name="Количество оплаченных занятий"
    )
    next_lesson_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Дата следующего занятия"
    )
    paid_till = models.DateField(blank=True, null=True, verbose_name="Оплачено до")
    note = models.TextField(blank=True, null=True, verbose_name="Примечание")
    paid_lesson_count = models.IntegerField(
        blank=True, null=True, verbose_name="Количество оплаченных занятий"
    )
    has_scheduled_lessons = models.BooleanField(
        default=False, verbose_name="Есть запланированные уроки"
    )

    def __str__(self):
        return f"Клиент {self.crm_id or 'без ID'} (Родитель: {self.user})"

    class Meta:
        db_table = "clients"
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

