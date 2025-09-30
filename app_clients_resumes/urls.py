from django.urls import path
from . import views

app_name = 'app_clients_resumes'

urlpatterns = [
    path('', views.index, name='index'),
]