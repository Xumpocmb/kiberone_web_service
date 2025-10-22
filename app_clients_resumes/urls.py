from django.urls import path
from app_clients_resumes.views import TutorRegisterView, TutorLoginView, TutorGroupsView, GroupClientsView, ClientResumesView, ResumeUpdateView, ResumeVerifyView, UnverifiedResumesView

app_name = 'app_clients_resumes'

urlpatterns = [
    # path('', views.index, name='index'),
    path("register/", TutorRegisterView.as_view(), name="register_tutor"),
    path("login/", TutorLoginView.as_view(), name="login_tutor"),
    path("groups/", TutorGroupsView.as_view(), name="tutor_groups"),
    path("group-clients/", GroupClientsView.as_view(), name="group_clients"),
    path("client-resumes/", ClientResumesView.as_view(), name="client_resumes"),
    path("resume/<int:resume_id>/", ResumeUpdateView.as_view(), name="resume_update"),
    path("resume/<int:resume_id>/verify/", ResumeVerifyView.as_view(), name="resume_verify"),
    path("unverified-resumes/", UnverifiedResumesView.as_view(), name="unverified_resumes"),
]
