from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import TutorProfile, Resume


# Инлайн для профиля тьютора в админке пользователя
class TutorProfileInline(admin.StackedInline):
    model = TutorProfile
    can_delete = False
    verbose_name = "Профиль тьютора"
    verbose_name_plural = "Профили тьюторов"


# Расширяем админку пользователя
class UserAdmin(BaseUserAdmin):
    inlines = (TutorProfileInline,)


# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Регистрируем TutorProfile отдельно для удобства
@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tutor_name', 'tutor_crm_id')
    search_fields = ('user__username', 'tutor_name', 'tutor_crm_id')
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Информация о тьюторе', {
            'fields': ('tutor_name', 'tutor_crm_id')
        }),
    )

# Регистрируем Resume
@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('student_crm_id', 'author', 'is_verified', 'created_at', 'updated_at')
    list_filter = ('is_verified', 'author', 'created_at', 'updated_at')
    search_fields = ('student_crm_id', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основная информация', {
            'fields': ('student_crm_id', 'author', 'content')
        }),
        ('Статус', {
            'fields': ('is_verified',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
