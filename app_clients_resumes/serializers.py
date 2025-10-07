import email
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import TutorProfile
from app_kiberclub.models import Branch
from app_api.alfa_crm_service.crm_service import get_teacher

class TutorRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    tutor_branch = serializers.IntegerField(required=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def validate_tutor_branch(self, value):
        if not Branch.objects.filter(branch_id=str(value)).exists():
            raise serializers.ValidationError("Филиал с указанным ID не существует.")
        return value

    def create(self, validated_data):
        username = validated_data['username']
        password = validated_data['password']
        tutor_branch_id = validated_data['tutor_branch']

        # Получаем tutor_crm_id из CRM API по номеру телефона (username)
        crm_response = get_teacher(tutor_branch_id, username)
        tutor_crm_id = None
        tutor_crm_name = None
        if crm_response and crm_response.get('items') and len(crm_response['items']) > 0:
            tutor_crm_id = crm_response['items'][0].get('id', None)
            tutor_crm_name = crm_response['items'][0].get('name', None)

        # Создаём пользователя
        user = User.objects.create_user(
            username=username,
            password=password,
            email='',
            is_staff=False,  # не даём доступ в админку по умолчанию
            is_superuser=False
        )

        # Определяем группу Tutor по умолчанию
        group = Group.objects.get(name='Tutor')
        user.groups.add(group)

        # Получаем объект филиала
        branch = Branch.objects.get(branch_id=str(tutor_branch_id))

        # Создаём профиль тьютора
        TutorProfile.objects.create(
            user=user, 
            tutor_crm_id=tutor_crm_id,
            tutor_name=tutor_crm_name,
            branch=branch
        )

        return user
