from django.urls import path
from app_api.views import (
    find_user_by_phone_view,
    find_user_in_db_view,
    get_bonus_by_id_view,
    get_client_bonuses,
    get_clients_by_user,
    get_location_by_id,
    get_sales_managers_by_branch,
    get_social_links,
    get_user_lessons_view,
    register_user_in_db_view,
    register_user_in_crm_view,
    create_or_update_clients_in_db_view,
    get_all_questions,
    get_answer_by_question_id,
    get_erip_payment_help,
    get_partner_categories_view,
    get_partners_by_category_view,
    get_partner_by_id_view, get_manager_by_room_id, get_user_balances,
)

app_name = "app_crm_api"

urlpatterns = [
    path("find_user_in_crm/", find_user_by_phone_view, name="find_user"),
    path("find_user_in_db/", find_user_in_db_view, name="find_user_in_db"),
    path("register_user_in_db/", register_user_in_db_view, name="register_user_in_db"),
    path("register_user_in_crm/", register_user_in_crm_view, name="register_user_in_crm"),
    path("create_or_update_clients_in_db/", create_or_update_clients_in_db_view, name="create_or_update_clients_in_db",),
    path("questions/", get_all_questions, name="questions"),
    path("answer_by_question/<int:question_id>/", get_answer_by_question_id, name="answer_by_question",),
    path("get_erip_payment_help/", get_erip_payment_help, name="get_erip_payment_help",),
    path("get_partner_categories/", get_partner_categories_view, name="get_partner_categories",),
    path("get_partners_by_category/<int:category_id>/", get_partners_by_category_view, name="get_partners_by_category",),
    path("get_partner_by_id/<int:partner_id>/", get_partner_by_id_view, name="get_partner_by_id",),
    path("get_client_bonuses/", get_client_bonuses, name="get_client_bonuses"),
    path("get_bonus_by_id/<int:bonus_id>/", get_bonus_by_id_view, name="get_bonus_by_id",),
    path("get_sales_managers_by_branch/<int:branch_id>/", get_sales_managers_by_branch, name="get_sales_managers_by_branch",),
    path("get_clients_by_user/<int:user_id>/", get_clients_by_user, name="get_clients_by_user",),
    path("get_social_links/", get_social_links, name="get_social_links"),
    path("get_user_lessons/", get_user_lessons_view, name="get_user_lessons"),
    path("get_location_by_id/<int:location_id>/", get_location_by_id, name="get_location_by_id",),
    path("get_manager_by_room_id/<int:room_id>/", get_manager_by_room_id, name="get_manager_by_room_id"),
    path("get_user_balances/", get_user_balances, name="get_user_balances"),

]
