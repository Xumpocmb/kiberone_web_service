from rest_framework import serializers
from app_kiberclub.models import Branch
from app_api.alfa_crm_service.crm_service import get_teacher
from .models import TutorProfile, ParentReview, Resume


class ParentReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentReview
        fields = '__all__'


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_verified')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Исключаем поле resume_type, так как оно больше не существует в модели
        if 'resume_type' in self.fields:
            del self.fields['resume_type']

class TutorRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    tutor_branch = serializers.IntegerField(required=True)

    def validate_username(self, value):
        if TutorProfile.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def validate_tutor_branch(self, value):
        if not Branch.objects.filter(branch_id=str(value)).exists():
            raise serializers.ValidationError("Филиал с указанным ID не существует.")
        return value

    def create(self, validated_data):
        username = validated_data['username']
        tutor_branch_id = validated_data['tutor_branch']

        # Получаем tutor_crm_id из CRM API по номеру телефона (username)
        crm_response = get_teacher(tutor_branch_id, username)
        if crm_response.get("total", 0) == 0:
            raise serializers.ValidationError({"error": "Тьютор не найден в CRM."})

        tutor_crm_id = None
        tutor_crm_name = None
        if crm_response and crm_response.get('items') and len(crm_response['items']) > 0:
            tutor_crm_id = crm_response['items'][0].get('id', None)
            tutor_crm_name = crm_response['items'][0].get('name', None)

        # Получаем объект филиала
        branch = Branch.objects.get(branch_id=str(tutor_branch_id))

        # Создаём профиль тьютора
        tutor_profile = TutorProfile.objects.create(
            username=username,
            tutor_crm_id=tutor_crm_id,
            tutor_name=tutor_crm_name,
            branch=branch
        )

        return tutor_profile


class TutorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TutorProfile
        fields = '__all__'
