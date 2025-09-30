from django.urls import reverse
from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase
from rest_framework import status

from app_clients_resumes.models import TutorProfile


class ClientsResumesAPITests(APITestCase):
    def setUp(self):
        # Убедимся, что группа Tutor существует, иначе регистрация упадёт
        Group.objects.get_or_create(name='Tutor')

    def test_register_tutor_success(self):
        url = reverse('app_clients_resumes:register_tutor')
        payload = {
            'username': 'new_tutor',
            'password': 'StrongPass123',
            'email': 'tutor@example.com',
            'tutor_crm_id': 'CRM123',
            'role': 'tutor',
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

        # Проверяем, что пользователь создан
        user = User.objects.get(username='new_tutor')
        self.assertIsNotNone(user)

        # Проверяем, что профиль тьютора создан
        profile = TutorProfile.objects.get(user=user)
        self.assertEqual(profile.tutor_crm_id, 'CRM123')

        # Проверяем, что пользователь добавлен в группу Tutor
        tutor_group = Group.objects.get(name='Tutor')
        self.assertTrue(user.groups.filter(id=tutor_group.id).exists())

    def test_register_tutor_duplicate_username_error(self):
        # Предварительно создаём пользователя
        User.objects.create_user(username='existing_user', password='pass123')
        url = reverse('app_clients_resumes:register_tutor')
        payload = {
            'username': 'existing_user',
            'password': 'StrongPass123',
            'email': 'existing@example.com',
            'role': 'tutor',
        }
        response = self.client.post(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_login_success(self):
        # Создаем пользователя
        User.objects.create_user(username='john', password='secret123')
        url = reverse('app_clients_resumes:login')
        payload = {'username': 'john', 'password': 'secret123'}
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'john')

    def test_login_invalid_credentials(self):
        User.objects.create_user(username='john', password='secret123')
        url = reverse('app_clients_resumes:login')
        payload = {'username': 'john', 'password': 'wrongpass'}
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_success(self):
        # Логиним пользователя
        User.objects.create_user(username='jane', password='secret123')
        login_url = reverse('app_clients_resumes:login')
        logout_url = reverse('app_clients_resumes:logout')
        self.client.post(login_url, data={'username': 'jane', 'password': 'secret123'})

        # Выходим
        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_csrf_token_endpoint(self):
        url = reverse('app_clients_resumes:csrf_token') if False else '/api/tutor/csrf/'
        # В urls нет имени для csrf, поэтому используем путь напрямую
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrfToken', response.json())
