from django.contrib import admin
from .models import TutorProfile, Resume, ParentReview


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'tutor_name', 'tutor_crm_id', 'branch', 'is_senior')
    search_fields = ('username', 'tutor_name', 'tutor_crm_id')
    list_filter = ('branch', 'is_senior')
    fieldsets = (
        ('Данные тьютора', {
            'fields': ('username', 'tutor_name', 'tutor_crm_id', 'branch', 'is_senior')
        }),
    )

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('student_crm_id', 'is_verified', 'created_at', 'updated_at')
    list_filter = ('is_verified', 'created_at', 'updated_at')
    search_fields = ('student_crm_id', 'content')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основная информация', {
            'fields': ('student_crm_id', 'content')
        }),
        ('Статус', {
            'fields': ('is_verified',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ParentReview)
class ParentReviewAdmin(admin.ModelAdmin):
    list_display = ('student_crm_id', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('student_crm_id', 'content')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основная информация', {
            'fields': ('student_crm_id', 'content')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
