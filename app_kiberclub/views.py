from django.shortcuts import render

from app_kiberclub.models import AppUser, Client


def index(request):
    context = {
        "title": "KIBERone",
    }
    telegram_id_from_req: str = request.GET.get('user_tg_id')

    bot_user = AppUser.objects.get(telegram_id=telegram_id_from_req)
    user_clients = Client.objects.filter(user=bot_user)
    context.update({"profiles": user_clients})
    return render(request, 'app_kiberclub/greetings.html', context=context)
