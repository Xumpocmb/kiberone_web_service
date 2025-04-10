from django.urls import path
from app_api.views import find_user_by_phone_view, find_user_in_db_view, register_user_in_db_view, register_user_in_crm_view, create_or_update_clients_in_db_view

app_name = 'app_crm_api'

urlpatterns = [
    path('find_user_in_crm/', find_user_by_phone_view, name='find_user'),
    path('find_user_in_db/', find_user_in_db_view, name='find_user_in_db'),
    path('register_user_in_db/', register_user_in_db_view, name='register_user_in_db'),
    path('register_user_in_crm/', register_user_in_crm_view, name='register_user_in_crm'),
    path('create_or_update_clients_in_db/', create_or_update_clients_in_db_view, name='create_or_update_clients_in_db'),

]
