from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_api.alfa_crm_service.crm_service import get_teacher_group, get_clients_in_group, get_all_groups
from .serializers import TutorRegistrationSerializer, TutorProfileSerializer
from .models import TutorProfile, Resume, ParentReview


class TutorRegisterView(APIView):
    """
    API endpoint для регистрации новых тьюторов.
    
    Позволяет создавать новые учетные записи тьюторов с открытым доступом.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Регистрация нового тьютора в системе",
        operation_summary="Регистрация тьютора",
        request_body=TutorRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Успешная регистрация",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успешной регистрации'),
                    }
                )
            ),
            400: openapi.Response(description="Ошибка валидации данных")
        },
        tags=['Регистрация']
    )
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
                "tutor_branch": 1
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


class TutorLoginView(APIView):
    """
    API endpoint для "входа" тьютора по username.
    Возвращает данные профиля, если тьютор найден.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Авторизация тьютора по username",
        operation_summary="Вход тьютора",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя (номер телефона)'),
            },
        ),
        responses={
            200: openapi.Response(description="Успешный вход", schema=TutorProfileSerializer),
            404: openapi.Response(description="Тьютор не найден"),
        },
        tags=['Авторизация']
    )
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({"error": "Необходимо указать username"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tutor_profile = TutorProfile.objects.get(username=username)
            serializer = TutorProfileSerializer(tutor_profile)
            response_data = serializer.data
            response_data['senior'] = tutor_profile.is_senior
            return Response(response_data)
        except TutorProfile.DoesNotExist:
            return Response({"error": "Тьютор с таким username не найден"}, status=status.HTTP_404_NOT_FOUND)


class TutorGroupsView(APIView):
    """
    API endpoint для получения списка групп тьютора.
    
    Возвращает список групп, в которых преподает тьютор.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Получение списка групп тьютора",
        operation_summary="Список групп тьютора",
        manual_parameters=[
            openapi.Parameter(
                'username',
                openapi.IN_QUERY,
                description="Username тьютора",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешное получение списка групп",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус операции'),
                        'groups': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID группы'),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Название группы'),
                                }
                           )
                       )
                    }
                )
            ),
            400: openapi.Response(description="Профиль тьютора не настроен"),
            404: openapi.Response(description="Профиль тьютора не найден"),
            500: openapi.Response(description="Внутренняя ошибка сервера")
        },
        tags=['Группы']
    )
    def get(self, request):
        """
        Обрабатывает GET запрос для получения групп тьютора.
        
        Args:
            request: HTTP запрос
            
        Returns:
            Response: JSON ответ с результатом операции:
                - При успехе: статус 200 со списком групп
                - При ошибке: статус 400/404 с описанием ошибки
                
        Example:
            GET /api/tutor/groups/?username=tutor123
            
            Response:
            {
                "success": true,
                "groups": [
                    {
                        "id": 123,
                        "name": "Группа Python"
                    }
                ]
            }
        """
        username = request.GET.get('username')
        if not username:
            return Response({"success": False, "message": "Параметр username обязателен"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Получаем профиль тьютора
            tutor_profile = TutorProfile.objects.get(username=username)



            
            if not tutor_profile.tutor_crm_id or not tutor_profile.branch:
                return Response({
                    "success": False,
                    "message": "Профиль тьютора не настроен полностью"
                }, status=status.HTTP_400_BAD_REQUEST)

            if tutor_profile.is_senior:
                crm_groups = get_all_groups()
            else:
                crm_groups = get_teacher_group(
                    branch=tutor_profile.branch.branch_id,
                    teacher_id=tutor_profile.tutor_crm_id,
                )

            groups_data = []
            if crm_groups:
                for group in crm_groups:
                    groups_data.append({
                        "id": group.get('id'),
                        "name": group.get('name'),
                    })

            return Response({
                "success": True,
                "groups": groups_data
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
    
    Возвращает список клиентов в указанной группе с их ID и именами.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Получение списка участников группы по ID группы",
        operation_summary="Список участников группы",
        manual_parameters=[
            openapi.Parameter(
                'group_id',
                openapi.IN_QUERY,
                description="ID группы для получения участников",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'branch',
                openapi.IN_QUERY,
                description="ID филиала",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешное получение списка участников",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус операции'),
                        'clients': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID клиента'),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя клиента')
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(description="Отсутствуют обязательные параметры"),
            500: openapi.Response(description="Ошибка при получении данных из CRM")
        },
        tags=['Группы']
    )
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
                        "id": 456,
                        "name": "Иван Иванов"
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
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Получение списка резюме клиента по ID ученика в CRM",
        operation_summary="Список резюме клиента",
        manual_parameters=[
            openapi.Parameter(
                'student_crm_id',
                openapi.IN_QUERY,
                description="ID ученика в CRM системе",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешное получение списка резюме",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус операции'),
                        'resumes': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID резюме'),
                                    'student_crm_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID ученика в CRM'),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING, description='Содержание резюме'),
                                    'is_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус верификации'),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата создания'),
                                    'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата обновления'),
                                }
                           )
                       )
                    }
                )
            ),
            400: openapi.Response(description="Отсутствует обязательный параметр student_crm_id"),
            500: openapi.Response(description="Ошибка при получении резюме")
        },
        tags=['Резюме']
    )
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
    API endpoint для обновления содержимого резюме.
    
    Позволяет обновлять текст резюме по его ID.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Обновление содержимого резюме по ID",
        operation_summary="Обновление резюме",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Новое содержание резюме'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Успешное обновление резюме",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус операции'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успехе'),
                        'resume': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID резюме'),
                                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Обновленное содержание'),
                                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата обновления')
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(description="Отсутствует обязательное поле content"),
            404: openapi.Response(description="Резюме не найдено"),
            500: openapi.Response(description="Ошибка при обновлении резюме")
        },
        tags=['Резюме']
    )
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
    API endpoint для верификации резюме.
    
    Позволяет изменять статус верификации резюме.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Изменение статуса верификации резюме",
        operation_summary="Верификация резюме",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['tutor_crm_id'],
            properties={
                'tutor_crm_id': openapi.Schema(type=openapi.TYPE_STRING, description='CRM ID тьютора'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Успешное изменение статуса верификации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус операции'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успехе'),
                    }
                )
            ),
            400: openapi.Response(description="Отсутствует обязательное поле is_verified"),
            404: openapi.Response(description="Резюме не найдено"),
            500: openapi.Response(description="Ошибка при изменении статуса верификации")
        },
        tags=['Резюме']
    )
    def post(self, request, resume_id):
        """
        Обрабатывает POST запрос для отметки резюме как проверенного.
        
        Args:
            request: HTTP запрос
            resume_id: ID резюме для верификации
            
        Returns:
            Response: JSON ответ с результатом операции
        """
        try:
            tutor_crm_id = request.data.get('tutor_crm_id')
            if not tutor_crm_id:
                return Response({"error": "Необходимо указать tutor_crm_id"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                tutor_profile = TutorProfile.objects.get(tutor_crm_id=tutor_crm_id)
            except TutorProfile.DoesNotExist:
                return Response({"error": "Тьютор с таким CRM ID не найден"}, status=status.HTTP_404_NOT_FOUND)

            if not tutor_profile.is_senior:
                return Response({"error": "Доступ запрещен. Требуется статус старшего тьютора."}, status=status.HTTP_403_FORBIDDEN)

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
            }

            return Response({
                "success": True,
                "message": "Резюме отмечено как проверенное"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при верификации резюме: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnverifiedResumesView(APIView):
    """
    API endpoint для получения списка непроверенных резюме.
    
    Возвращает все резюме, у которых is_verified = false.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Получение списка непроверенных резюме",
        operation_summary="Список непроверенных резюме",
        responses={
            200: openapi.Response(
                description="Успешное получение списка непроверенных резюме",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус операции'),
                        'resumes': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID резюме'),
                                    'student_crm_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID ученика в CRM'),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING, description='Содержание резюме'),
                                    'is_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус верификации'),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата создания'),
                                    'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата обновления'),
                                }
                           )
                       )
                    }
                )
            ),
            500: openapi.Response(description="Ошибка при получении резюме")
        },
        tags=['Резюме']
    )
    def get(self, request):
        """
        Обрабатывает GET запрос для получения списка непроверенных резюме.
        
        Args:
            request: HTTP запрос
            
        Returns:
            Response: JSON ответ со списком непроверенных резюме или ошибкой
        """
        try:
            # Получаем все резюме, у которых is_verified = false
            resumes = Resume.objects.filter(is_verified=False).order_by('-created_at')
            
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
                })
            
            return Response({
                "success": True,
                "resumes": resumes_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при получении непроверенных резюме: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentReviewView(APIView):
    """
    API endpoint для получения отзыва родителя по ID ученика.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Получение отзыва родителя по ID ученика в CRM",
        operation_summary="Отзыв родителя",
        manual_parameters=[
            openapi.Parameter(
                'student_crm_id',
                openapi.IN_PATH,
                description="ID ученика в CRM системе",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешное получение отзыва родителя",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус операции'),
                        'review': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID отзыва'),
                                'student_crm_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID ученика в CRM'),
                                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Содержание отзыва'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата создания'),
                                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Дата обновления'),
                            }
                        )
                    }
                )
            ),
            404: openapi.Response(description="Отзыв родителя не найден"),
            50: openapi.Response(description="Ошибка при получении отзыва")
        },
        tags=['Отзывы']
    )
    def get(self, request, student_crm_id):
        """
        Обрабатывает GET запрос для получения отзыва родителя по ID ученика.
        
        Args:
            request: HTTP запрос
            student_crm_id: ID ученика в CRM
            
        Returns:
            Response: JSON ответ с отзывом родителя или ошибкой
        """
        try:
            # Получаем отзыв родителя по ID ученика
            parent_review = ParentReview.objects.get(student_crm_id=student_crm_id)
            
            # Формируем данные отзыва
            review_data = {
                "id": parent_review.id,
                "student_crm_id": parent_review.student_crm_id,
                "content": parent_review.content,
                "created_at": parent_review.created_at.isoformat(),
                "updated_at": parent_review.updated_at.isoformat(),
            }
            
            return Response({
                "success": True,
                "review": review_data
            }, status=status.HTTP_200_OK)
            
        except ParentReview.DoesNotExist:
            return Response({
                "success": False,
                "message": "Отзыв родителя не найден"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Ошибка при получении отзыва родителя: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
