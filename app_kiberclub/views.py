from django.shortcuts import render

def index(request):
    context = {
        "title": "KIBERone",
    }
    telegram_id = request.GET.get('user_tg_id')
    context.update({"tg_id": telegram_id})
    return render(request, 'app_kiberclub/greetings.html', context=context)
