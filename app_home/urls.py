from django.urls import path
from . import views

app_name = 'app_home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('add-student/', views.add_student_view, name='add_student'),
    path('ajax/load-locations/', views.load_locations, name='ajax_load_locations'),
]