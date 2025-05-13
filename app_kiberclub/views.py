import json

import gspread
import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from oauth2client.service_account import ServiceAccountCredentials

from app_api.alfa_crm_service.crm_service import get_client_lessons, get_client_lesson_name
from app_kiberclub.models import AppUser, Client, Location
from app_kibershop.models import ClientKiberons

from googleapiclient.discovery import build
from google.oauth2 import service_account

CREDENTIALS_FILE = 'kiberone-tg-bot-a43691efe721.json'


def index(request: HttpRequest) -> HttpResponse:
    context = {
        "title": "KIBERone",
    }

    try:
        telegram_id_from_req = request.GET.get("user_tg_id")
        if telegram_id_from_req:
            request.session["tg_id"] = telegram_id_from_req
        else:
            telegram_id_from_req = request.session.get("tg_id")
            if not telegram_id_from_req:
                return redirect("app_kiberclub:error_page")

        bot_user = get_object_or_404(AppUser, telegram_id=telegram_id_from_req)
        user_clients = Client.objects.filter(user=bot_user)
        context.update({"profiles": user_clients})

    except AppUser.DoesNotExist:
        return redirect("app_kiberclub:error_page")
    except Exception as e:
        return redirect("app_kiberclub:error_page")

    return render(request, 'app_kiberclub/index.html', context=context)



def open_profile(request):
    """
        Отображает профиль выбранного клиента.
        """
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        if client_id:
            request.session['client_id'] = client_id
        else:
            print("not client id")
            return redirect('app_kiberclub:error_page')
    else:
        client_id = request.session.get('client_id')

    try:
        client = get_object_or_404(Client, crm_id=client_id)
        context = {
            "title": "KIBERone - Профиль",
            "client": {
                "client_id": client_id,
                "crm_id": client.crm_id,
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
                "has_scheduled_lessons": "Да" if client.has_scheduled_lessons else "Нет"
            }
        }

        portfolio_link = get_portfolio_link(client.name)
        context.update({"portfolio_link": portfolio_link})

        branch_id = int(client.branch.branch_id)

        lessons_data = get_client_lessons(client_id, branch_id, lesson_status=1, lesson_type=2)
        if lessons_data and lessons_data.get("total", 0) > 0:
            lesson = lessons_data.get("items", [])[-1]
            room_id = lesson.get("room_id")
            subject_id = lesson.get("subject_id")


            lesson_info = get_client_lesson_name(branch_id, subject_id)
            if lesson_info.get("total") > 0:
                all_lesson_items: list = lesson_info.get("items")
                lesson_name = ""
                for item in all_lesson_items:
                    if item.get("id") == subject_id:
                        lesson_name = item.get("name", "")

            if room_id:

                request.session["room_id"] = room_id

                location = Location.objects.filter(location_crm_id=room_id).first()
                location_sheet_name = location.sheet_name


                client_resume = get_resume_from_google_sheet(client.branch.sheet_url, location_sheet_name, client.crm_id)
                context["client"].update({
                    "location_name": location.name,
                    "lesson_name": lesson_name if lesson_name else "",
                    "resume": client_resume if client_resume else "Появится позже",
                    "room_id": room_id,
                })

                # ----------------------------------------------------------------

                with open("kiberclub_credentials.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                    baranovichi_login: str = data["Барановичи"]["логин"]
                    baranovichi_password: str = data["Барановичи"]["пароль"]

                    minsk_login: str = data["Минск"]["логин"]
                    minsk_password: str = data["Минск"]["пароль"]

                    borisov_login: str = data["Борисов"]["логин"]
                    borisov_password: str = data["Борисов"]["пароль"]

                    novopolock_login: str = data["Новополоцк"]["логин"]
                    novopolock_password: str = data["Новополоцк"]["пароль"]

                user_crm_name_splitted: list = client.name.split(" ", )[:2]
                user_crm_name_full: str = " ".join(user_crm_name_splitted).strip()

                if branch_id == 1:
                    login = minsk_login
                    password = minsk_password
                    kiberons: str | None = get_kiberons_count(client.crm_id, user_crm_name_full, login, password)
                elif branch_id == 3:
                    login = borisov_login
                    password = borisov_password
                    kiberons: str | None = get_kiberons_count(client.crm_id, user_crm_name_full, login, password)
                elif branch_id == 2:
                    login = baranovichi_login
                    password = baranovichi_password
                    kiberons: str | None = get_kiberons_count(client.crm_id, user_crm_name_full, login, password)
                elif branch_id == 4:
                    login = novopolock_login
                    password = novopolock_password
                    kiberons: str | None = get_kiberons_count(client.crm_id, user_crm_name_full, login, password)

                context["client"].update({
                    "kiberons_count": kiberons if kiberons else "0",
                })
            else:
                return redirect("app_kiberclub:error_page")
            return render(request, "app_kiberclub/client_card.html", context)
        else:
            return redirect("app_kiberclub:error_page")
    except Exception as e:
        print(e)
        return redirect('app_kiberclub:error_page')



def error_page_view(request):
    return render(request, 'app_kiberclub/error_page.html')


def get_resume_from_google_sheet(sheet_url: str, sheet_name: str, child_id: str):
    """
    Загружает резюме ребенка из Google Таблицы.
    """
    credentials_path = CREDENTIALS_FILE

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(credentials)

    try:
        sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    except Exception as e:
        return "Появится позже"

    data = sheet.get_all_records()

    for row in data:
        if str(row.get("ID ребенка")) == str(child_id):
            resume = row.get("Резюме май 2025", "")
            return resume.strip()

    return "Появится позже"



def save_review_from_page(request):
    if request.method == "POST":
        crm_id = request.POST.get("crm_id")
        room_id = request.POST.get("room_id")
        feedback = request.POST.get('feedbackInput')

        client = get_object_or_404(Client, crm_id=crm_id)
        location = Location.objects.filter(location_crm_id=room_id).first()
        location_sheet_name = location.sheet_name

        success = save_review_to_google_sheet(
            sheet_url=client.branch.sheet_url,
            sheet_name=location_sheet_name,
            child_id=client.crm_id,
            feedback=feedback
        )
        if success:
            return JsonResponse({'status': 'success', "message": "Ваш отзыв сохранен!"}, status=200)
        else:
            return JsonResponse({'status': 'error', "message": "Произошла ошибка при сохранении отзыва"}, status=400)



def save_review_to_google_sheet(sheet_url: str, sheet_name: str, child_id: str, feedback: str):
    """
    Сохраняет отзыв родителя в Google Таблицу.
    """
    credentials_path = CREDENTIALS_FILE

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(credentials)

    try:
        sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    except Exception as e:
        print(f"Ошибка при открытии таблицы: {e}")
        return False

    headers = sheet.row_values(1)
    try:
        feedback_column_index = headers.index("Отзыв родителя") + 1
    except ValueError:
        print("Столбец 'Отзыв родителя' не найден в таблице.")
        return False

    data = sheet.get_all_records()
    for index, row in enumerate(data, start=2):
        if str(row.get("ID ребенка")) == str(child_id):
            try:
                feedback = str(feedback).strip()
                if not feedback:
                    print("Отзыв пустой. Пропускаем обновление.")
                    return False

                cell = f"{gspread.utils.rowcol_to_a1(index, feedback_column_index)}"
                sheet.update(cell, [[feedback]])
                return True
            except Exception as e:
                print(f"Ошибка при обновлении ячейки: {e}")
                return False

    print(f"Ребенок с ID {child_id} не найден в таблице.")
    return False



def get_kiberons_count(user_crm_id, user_crm_name_full: str, login: str, password: str) -> str | None:
    cookies = {
        'developsess': 'e65294731ff311d892841471f7beec1e',
    }
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        # 'cookie': 'developsess=e65294731ff311d892841471f7beec1e',
        'origin': 'https://kiber-one.club',
        'priority': 'u=0, i',
        'referer': 'https://kiber-one.club/',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }

    data = {
        'urltogo': 'https://kiber-one.club/enter/',
        'login': login,
        'password': password,
        'sendloginform': 'Войти',
    }
    response = requests.post('https://kiber-one.club/enter/', cookies=cookies, headers=headers, data=data)

    if response.status_code != 200:
        return None

    cookies.update(response.cookies)
    headers.update(response.headers)
    users_url = "https://kiber-one.club/mycabinet/users/"

    try:
        response = requests.get(users_url, cookies=cookies, headers=headers)

        if response.status_code != 200:
            return None
    except Exception as e:
        return None

    try:
        soup = BeautifulSoup(response.text, 'lxml')
        if soup is None:
            return None
    except Exception as e:
        return None

    children_elements = soup.find_all("div", class_="user_item")
    if not children_elements:
        print("No children elements found")
        return None

    for child in children_elements:
        name_element = child.find('div', class_='user_admin_col_name').find('a')
        full_name = name_element.text.strip()
        full_name_splitted = full_name.split(' ')[:2]
        name = ' '.join(full_name_splitted)
        if name == ' '.join(user_crm_name_full.split(' ')[:2]):
            balance_element = child.find('div', class_='user_admin_col_balance')
            balance = balance_element.text.strip()

            user = Client.objects.filter(crm_id=user_crm_id).first()
            if not user:
                print("user not found")
                return "0"
            user_kiberons_in_db = ClientKiberons.objects.filter(client=user).first()
            if user_kiberons_in_db:
                user_kiberons_in_db.start_kiberons_count = balance
                user_kiberons_in_db.save()
            else:
                ClientKiberons.objects.create(client=user, start_kiberons_count=balance)

            return balance
    return None



def get_portfolio_link(client_name) -> str | None:
    SCOPES = ['https://www.googleapis.com/auth/drive ']
    CREDENTIALS_FILE = 'portfolio-credentials.json'
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)

    drive_service = build('drive', 'v3', credentials=credentials)

    client_name = " ".join(client_name.split(" ")[:2])
    query = f"name contains '{client_name}' and mimeType='application/vnd.google-apps.folder'"
    results = drive_service.files().list(
        q=query,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()

    folders = results.get('files', [])
    if not folders:
        return "#"

    folder_id = folders[0]['id']
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    return folder_url