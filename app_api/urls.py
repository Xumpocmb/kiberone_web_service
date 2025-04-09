from django.urls import path
from app_api.views import find_user_by_phone_view, find_user_in_db_view, register_user_in_db_view, register_user_in_crm_view

app_name = 'app_crm_api'

urlpatterns = [
    path('find_user_in_crm/', find_user_by_phone_view, name='find_user'),
    path('find_user_in_db/', find_user_in_db_view, name='find_user_in_db'),
    path('register_user_in_db/', register_user_in_db_view, name='register_user_in_db'),
    path('register_user_in_crm/', register_user_in_crm_view, name='register_user_in_crm'),

]
