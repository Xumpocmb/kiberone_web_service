from django.urls import path
from app_clients_resumes.views import TutorRegisterView, LoginView, LogoutView, TutorGroupsView, GroupClientsView, csrf_token

app_name = 'app_clients_resumes'

urlpatterns = [
    # path('', views.index, name='index'),
    path("register/", TutorRegisterView.as_view(), name="register_tutor"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("groups/", TutorGroupsView.as_view(), name="tutor_groups"),
    path("group-clients/", GroupClientsView.as_view(), name="group_clients"),
    path('csrf/', csrf_token),
]
