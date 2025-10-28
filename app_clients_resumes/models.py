from django.db import models
from app_kiberclub.models import Branch


class TutorProfile(models.Model):
    username = models.CharField("Username", max_length=150, unique=True, null=True, blank=True)
    tutor_crm_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="CRM ID тьютора"
    )
    tutor_name = models.CharField("Имя тьютора", max_length=200, blank=True, null=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        verbose_name="Филиал",
        null=True,
        blank=True
    )
    is_senior = models.BooleanField("Старший тьютор", default=False)

    def __str__(self):
        return f"Профиль тьютора: {self.username}"


class Resume(models.Model):
    student_crm_id = models.CharField("ID ученика", max_length=10)
    resume_type = models.CharField("Тип резюме", max_length=1000, blank=True, null=True)
    content = models.TextField("Содержание резюме", max_length=5000, blank=True, null=True)
    is_verified = models.BooleanField("Проверено", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"
        permissions = [
            ("can_verify_resume", "Может отмечать резюме как проверенное"),
        ]

    def __str__(self):
        return f"Резюме ученика {self.student_crm_id}"


class ParentReview(models.Model):
    student_crm_id = models.CharField("ID ученика", max_length=10)
    content = models.TextField("Отзыв родителя", max_length=5000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отзыв родителя"
        verbose_name_plural = "Отзывы родителей"

    def __str__(self):
        return f"Отзыв родителя для ученика {self.student_crm_id}"
