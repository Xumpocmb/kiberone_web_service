
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
    permission_classes = []

    def post(self, request):
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
    def post(self, request):
        logout(request)
        return Response({"message": "Выход выполнен"})


class TutorRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TutorRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Тьютор успешно зарегистрирован!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

def csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})
