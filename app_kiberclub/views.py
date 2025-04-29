from django.shortcuts import render, redirect, get_object_or_404

from app_api.alfa_crm_service.crm_service import get_client_lessons
from app_api.views import get_user_lessons_view
from app_kiberclub.models import AppUser, Client, Location


def index(request):
    context = {
        "title": "KIBERone",
    }
    telegram_id_from_req: str = request.GET.get('user_tg_id')

    bot_user = AppUser.objects.get(telegram_id=telegram_id_from_req)
    user_clients = Client.objects.filter(user=bot_user)
    context.update({"profiles": user_clients})
    return render(request, 'app_kiberclub/greetings.html', context=context)



def open_profile(request):
    """
        Отображает профиль выбранного клиента.
        Ожидается GET-параметр 'crm_id' с идентификатором клиента.
        """
    # Получаем crm_id из GET-параметров
    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        if not profile_id:
            return redirect('app_kiberclub:error_page')

        try:
            client = get_object_or_404(Client, crm_id=profile_id)

            branch_id = int(client.branch.branch_id)

            lessons_data = get_client_lessons(profile_id, branch_id, lesson_status=1, lesson_type=2)
            if lessons_data and lessons_data.get("total", 0) > 0:
                lesson = lessons_data.get("items", [])[0]
                room_id = lesson.get("room_id")

                location = Location.objects.filter(location_crm_id=room_id).first()

                print(location.name)


                context = {
                    "title": "KIBERone - Профиль",
                    "client": {
                        "name": client.name,
                        "dob": client.dob.strftime("%d.%m.%Y") if client.dob else "Не указано",
                        "balance": client.balance,
                        "paid_count": client.paid_lesson_count,
                        "next_lesson_date": client.next_lesson_date.strftime(
                            "%d.%m.%Y") if client.next_lesson_date else "Нет запланированных уроков",
                        "paid_till": client.paid_till.strftime("%d.%m.%Y") if client.paid_till else "Не указано",
                        "note": client.note or "Нет заметок",
                        "branch": client.branch.name if client.branch else "Не указано",
                        "is_study": "Да" if client.is_study else "Нет",
                        "has_scheduled_lessons": "Да" if client.has_scheduled_lessons else "Нет",

                        "location_name": location.name,
                    },
                }
            return render(request, "app_kiberclub/client_card.html", context)
        except Exception as e:
            print(e)
            return redirect('app_kiberclub:error_page')
    else:
        return redirect('app_kiberclub:error_page')



def error_page_view(request):
    return render(request, 'app_kiberclub/error_page.html')