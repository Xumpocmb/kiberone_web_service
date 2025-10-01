from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.middleware.csrf import get_token
from django.http import JsonResponse
from .serializers import TutorRegistrationSerializer


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
                "username": "tutor123",
                "password": "password123",
                "email": "tutor@example.com",
                "first_name": "Иван",
                "last_name": "Петров"
            }
        """
        serializer = TutorRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Тьютор успешно зарегистрирован!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

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
