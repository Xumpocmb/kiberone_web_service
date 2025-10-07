from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.middleware.csrf import get_token
from django.http import JsonResponse
from .serializers import TutorRegistrationSerializer
from .models import TutorProfile
from app_api.alfa_crm_service.crm_service import get_teacher_group, get_clients_in_group


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    """
    API endpoint для аутентификации пользователей.
    
    Предоставляет функционал входа в систему с проверкой CSRF токена.
    """
    permission_classes = []

    def post(self, request):
        """
        Обрабатывает POST запрос для входа пользователя в систему.
        
        Args:
            request: HTTP запрос с данными аутентификации
            
        Returns:
            Response: JSON ответ с результатом операции:
                - При успешном входе: статус 200 с данными пользователя
                - При ошибке: статус 400 с ошибками валидации
                
        Example:
            POST /api/tutor/login/
            {
                "username": "user123",
                "password": "password123"
            }
        """
        form = AuthenticationForm(data=request.data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return Response({
                "message": "Успешный вход",
                "user": {"id": user.id, "username": user.username}
            })
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API endpoint для выхода пользователя из системы.
    
    Обеспечивает безопасное завершение сессии пользователя.
    """
    
    def post(self, request):
        """
        Обрабатывает POST запрос для выхода пользователя из системы.
        
        Args:
            request: HTTP запрос с данными сессии
            
        Returns:
            Response: JSON ответ с подтверждением выхода (статус 200)
            
        Example:
            POST /api/tutor/logout/
            {}
        """
        logout(request)
        return Response({"message": "Выход выполнен"})


class TutorRegisterView(APIView):
    """
    API endpoint для регистрации новых тьюторов.
    
    Позволяет создавать новые учетные записи тьюторов с открытым доступом.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Обрабатывает POST запрос для регистрации нового тьютора.
        
        Args:
            request: HTTP запрос с данными для регистрации
            
        Returns:
            Response: JSON ответ с результатом операции:
                - При успешной регистрации: статус 201 с сообщением об успехе
                - При ошибке валидации: статус 400 с ошибками
                
        Example:
            POST /api/tutor/register/
            {
                "username": "tutor_phone_number",
                "password": "password123",
                "tutor_branch": 1
            }
            
        Note:
            - username используется как номер телефона для поиска в CRM
            - tutor_crm_id автоматически получается из CRM API
            - роль и группа "Tutor" назначаются по умолчанию
        """
        serializer = TutorRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Тьютор успешно зарегистрирован!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TutorGroupsView(APIView):
    """
    API endpoint для получения списка групп тьютора.
    
    Возвращает список групп, в которых преподает авторизованный тьютор.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Обрабатывает GET запрос для получения групп тьютора.
        
        Args:
            request: HTTP запрос от авторизованного пользователя
            
        Returns:
            Response: JSON ответ с результатом операции:
                - При успехе: статус 200 со списком групп
                - При ошибке: статус 400/404 с описанием ошибки
                
        Example:
            GET /api/tutor/groups/
            
            Response:
            {
                "success": true,
                "groups": [
                    {
                        "id": 123,
                        "name": "Группа Python",
                        "teacher_ids": ["teacher1", "teacher2"]
                    }
                ]
            }
        """
        try:
            # Получаем профиль тьютора
            tutor_profile = TutorProfile.objects.get(user=request.user)
            
            if not tutor_profile.tutor_crm_id or not tutor_profile.branch:
                return Response({
                    "success": False,
                    "message": "Профиль тьютора не настроен полностью"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем группы из CRM
            groups = get_teacher_group(
                branch=tutor_profile.branch.branch_id,
                teacher_id=tutor_profile.tutor_crm_id,
            )
            
            return Response({
                "success": True,
                "groups": groups
            }, status=status.HTTP_200_OK)
            
        except TutorProfile.DoesNotExist:
            return Response({
                "success": False,
                "message": "Профиль тьютора не найден"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при получении групп: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupClientsView(APIView):
    """
    API endpoint для получения списка участников группы.
    
    Требует авторизации. Возвращает список клиентов в указанной группе с их ID и именами.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получает список участников группы по group_id.
        
        Args:
            request: HTTP запрос с параметрами group_id и branch
            
        Returns:
            Response: JSON объект со списком участников группы
            
        Example:
            GET /api/tutor/group-clients/?group_id=123&branch=2
            
            Response:
                {
                    "success": true,
                    "clients": [
                        {
                            "customer_id": 6881,
                            "client_name": "Таранов Марк Алексеевич"
                        }
                    ]
                }
        """
        try:
            group_id = request.GET.get('group_id')
            branch = request.GET.get('branch')
            
            if not group_id:
                return Response({
                    "success": False,
                    "message": "Параметр group_id обязателен"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not branch:
                return Response({
                    "success": False,
                    "message": "Параметр branch обязателен"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем список участников группы из CRM
            clients = get_clients_in_group(group_id=group_id, branch=branch)
            
            return Response({
                "success": True,
                "clients": clients
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при получении участников группы: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def csrf_token(request):
    """
    Генерирует и возвращает CSRF токен для клиентских приложений.
    
    Args:
        request: HTTP запрос
        
    Returns:
        JsonResponse: JSON объект с CSRF токеном
        
    Example:
        GET /api/tutor/csrf/
        
        Response:
            {"csrfToken": "abc123def456..."}
    """
    return JsonResponse({'csrfToken': get_token(request)})
