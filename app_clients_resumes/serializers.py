from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import TutorProfile

class TutorRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False)
    tutor_crm_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[('tutor', 'Tutor'), ('senior', 'Senior Tutor')])

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def create(self, validated_data):
        username = validated_data['username']
        password = validated_data['password']
        email = validated_data.get('email', '')
        tutor_crm_id = validated_data.get('tutor_crm_id') or None
        role = validated_data['role']

        # Создаём пользователя
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_staff=False,  # не даём доступ в админку по умолчанию
            is_superuser=False
        )

        # Определяем группу
        group = Group.objects.get(name='Tutor')
        user.groups.add(group)

        # Создаём профиль тьютора
        TutorProfile.objects.create(user=user, tutor_crm_id=tutor_crm_id)

        return user
