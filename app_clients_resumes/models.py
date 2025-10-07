from django.db import models
from django.contrib.auth.models import User
from app_kiberclub.models import Branch


class TutorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tutor_profile')
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

    def __str__(self):
        return f"Профиль тьютора: {self.user.username}"


class Resume(models.Model):
    student_crm_id = models.CharField("ID ученика", max_length=10)
    resume_type = models.CharField("Тип резюме", max_length=100, blank=True, null=True)
    content = models.TextField("Содержание резюме", max_length=5000, blank=True, null=True)
    is_verified = models.BooleanField("Проверено", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resumes',
        verbose_name="Автор (тьютор)"
    )

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"
        permissions = [
            ("can_verify_resume", "Может отмечать резюме как проверенное"),
        ]

    def __str__(self):
        return f"Резюме ученика {self.student_crm_id} (автор: {self.author.username})"
