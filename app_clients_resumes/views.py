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
from .models import TutorProfile, Resume
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


class ClientResumesView(APIView):
    """
    API endpoint для получения списка резюме клиента.
    
    Возвращает все резюме для указанного клиента (по student_crm_id).
    Требует аутентификации пользователя.
    
    Authentication:
        - Требует активную сессию пользователя (session cookies)
        - Необходим CSRF токен в заголовке X-CSRFToken
        - При отсутствии аутентификации возвращает 403 Forbidden
    
    Methods:
        GET: Получить список резюме клиента
        
    Query Parameters:
        student_crm_id (str, required): ID ученика в CRM системе
        
    Returns:
        Response: JSON ответ со списком резюме
        
        Success (200 OK):
            {
                "success": true,
                "resumes": [
                    {
                        "id": 1,
                        "student_crm_id": "12345",
                        "content": "Содержание резюме...",
                        "is_verified": true,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-16T14:20:00Z",
                        "author": "tutor_username"
                    }
                ]
            }
            
        Empty result (200 OK):
            {
                "success": true,
                "resumes": []
            }
            
        Missing parameter (400 Bad Request):
            {
                "success": false,
                "message": "Параметр student_crm_id обязателен"
            }
            
        Authentication error (403 Forbidden):
            {
                "detail": "Учетные данные не были предоставлены."
            }
            
        Server error (500 Internal Server Error):
            {
                "success": false,
                "message": "Ошибка при получении резюме: <error_details>"
            }
            
    Examples:
        GET /api/tutor/client-resumes/?student_crm_id=12345
        
        curl -X GET "http://localhost:8000/api/tutor/client-resumes/?student_crm_id=12345" \
             -H "Cookie: sessionid=<session_id>; csrftoken=<csrf_token>" \
             -H "X-CSRFToken: <csrf_token>" \
             -H "Content-Type: application/json"
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Обрабатывает GET запрос для получения списка резюме клиента.
        
        Args:
            request: HTTP запрос с параметром student_crm_id
            
        Returns:
            Response: JSON ответ со списком резюме или ошибкой
        """
        try:
            student_crm_id = request.GET.get('student_crm_id')
            
            if not student_crm_id:
                return Response({
                    "success": False,
                    "message": "Параметр student_crm_id обязателен"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем все резюме для указанного ученика
            resumes = Resume.objects.filter(student_crm_id=student_crm_id).order_by('-created_at')
            
            # Формируем список резюме
            resumes_data = []
            for resume in resumes:
                resumes_data.append({
                    "id": resume.id,
                    "student_crm_id": resume.student_crm_id,
                    "content": resume.content,
                    "is_verified": resume.is_verified,
                    "created_at": resume.created_at.isoformat(),
                    "updated_at": resume.updated_at.isoformat(),
                    "author": resume.author.username
                })
            
            return Response({
                "success": True,
                "resumes": resumes_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при получении резюме: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeUpdateView(APIView):
    """
    API endpoint для сохранения/изменения резюме по его ID.
    
    Позволяет обновлять содержание резюме.
    Требует аутентификации пользователя.
    
    Methods:
        POST: Обновить резюме по ID
        
    URL Parameters:
        resume_id (int): ID резюме для обновления
        
    Request Body:
        {
            "content": "Новое содержание резюме"
        }
        
    Returns:
        Response: JSON ответ с результатом операции:
            {
                "success": true,
                "message": "Резюме успешно обновлено",
                "resume": {
                    "id": 1,
                    "student_crm_id": "12345",
                    "content": "Обновленное содержание резюме",
                    "is_verified": false,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-16T14:20:00Z",
                    "author": "tutor_username"
                }
            }
            
    Example:
        POST /api/tutor/resume/1/
        {
            "content": "Новое содержание резюме"
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        """
        Обрабатывает POST запрос для обновления резюме.
        
        Args:
            request: HTTP запрос с данными для обновления
            resume_id: ID резюме для обновления
            
        Returns:
            Response: JSON ответ с результатом операции
        """
        try:
            # Получаем резюме по ID
            try:
                resume = Resume.objects.get(id=resume_id)
            except Resume.DoesNotExist:
                return Response({
                    "success": False,
                    "message": f"Резюме с ID {resume_id} не найдено"
                }, status=status.HTTP_404_NOT_FOUND)

            # Получаем данные из запроса
            content = request.data.get('content')

            # Валидация обязательного поля content
            if content is None:
                return Response({
                    "success": False,
                    "message": "Поле 'content' обязательно"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Валидация длины контента
            if len(content) > 5000:
                return Response({
                    "success": False,
                    "message": "Содержание резюме не может превышать 5000 символов"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Обновляем поле content
            resume.content = content

            # Сохраняем изменения
            resume.save()

            # Формируем ответ с обновленными данными
            resume_data = {
                "id": resume.id,
                "student_crm_id": resume.student_crm_id,
                "content": resume.content,
                "is_verified": resume.is_verified,
                "created_at": resume.created_at.isoformat(),
                "updated_at": resume.updated_at.isoformat(),
                "author": resume.author.username
            }

            return Response({
                "success": True,
                "message": "Резюме успешно обновлено",
                "resume": resume_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при обновлении резюме: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeVerifyView(APIView):
    """
    API endpoint для отметки резюме как проверенного.
    
    Позволяет отмечать резюме как проверенное (is_verified = True).
    Доступен только пользователям из группы Senior Tutor.
    Требует аутентификации пользователя.
    
    Methods:
        POST: Отметить резюме как проверенное
        
    URL Parameters:
        resume_id (int): ID резюме для верификации
        
    Returns:
        Response: JSON ответ с результатом операции:
            {
                "success": true,
                "message": "Резюме отмечено как проверенное",
                "resume": {
                    "id": 1,
                    "student_crm_id": "12345",
                    "content": "Содержание резюме...",
                    "is_verified": true,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-16T14:20:00Z",
                    "author": "tutor_username"
                }
            }
            
    Example:
        POST /api/tutor/resume/1/verify/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        """
        Обрабатывает POST запрос для отметки резюме как проверенного.
        
        Args:
            request: HTTP запрос от авторизованного пользователя
            resume_id: ID резюме для верификации
            
        Returns:
            Response: JSON ответ с результатом операции
        """
        try:
            # Проверяем, что пользователь принадлежит к группе Senior Tutor
            if not request.user.groups.filter(name='Senior Tutor').exists():
                return Response({
                    "success": False,
                    "message": "Доступ запрещен. Требуется группа Senior Tutor"
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем резюме по ID
            try:
                resume = Resume.objects.get(id=resume_id)
            except Resume.DoesNotExist:
                return Response({
                    "success": False,
                    "message": f"Резюме с ID {resume_id} не найдено"
                }, status=status.HTTP_404_NOT_FOUND)

            # Проверяем, не отмечено ли резюме уже как проверенное
            if resume.is_verified:
                return Response({
                    "success": False,
                    "message": "Резюме уже отмечено как проверенное"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Отмечаем резюме как проверенное
            resume.is_verified = True
            resume.save()

            # Формируем ответ с обновленными данными
            resume_data = {
                "id": resume.id,
                "student_crm_id": resume.student_crm_id,
                "content": resume.content,
                "is_verified": resume.is_verified,
                "created_at": resume.created_at.isoformat(),
                "updated_at": resume.updated_at.isoformat(),
                "author": resume.author.username
            }

            return Response({
                "success": True,
                "message": "Резюме отмечено как проверенное",
                "resume": resume_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при верификации резюме: {str(e)}"
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
