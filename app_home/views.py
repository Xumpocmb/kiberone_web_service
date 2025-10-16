import gspread
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm
from django.core.files.storage import FileSystemStorage
import os
import pandas as pd
from django.conf import settings
from app_kiberclub.models import Location
from django.http import JsonResponse

@login_required(login_url='/users/login/')
def home_view(request):
    return render(request, 'app_home/home.html')

def load_locations(request):
    branch_id = request.GET.get('branch')
    locations = Location.objects.filter(branch_id=branch_id).order_by('name')
    return JsonResponse(list(locations.values('id', 'name', 'sheet_name')), safe=False)

@login_required(login_url='/users/login/')
def add_student_view(request):
    message = ''
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                branch = form.cleaned_data['branch']
                location = form.cleaned_data['location']
                uploaded_file = form.cleaned_data['file']

                # Сохранение файла
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp'))
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_path = os.path.join(settings.MEDIA_ROOT, 'temp', filename)

                # Обработка Excel
                excel_df = pd.read_excel(file_path)

                # Работа с Google Sheets
                CREDENTIALS_FILE = 'kiberone-tg-bot-a43691efe721.json'
                sheet_url = branch.sheet_url
                sheet_name = location.sheet_name

                account = gspread.service_account(filename=CREDENTIALS_FILE)
                spreadsheet = account.open_by_url(sheet_url)
                worksheet = spreadsheet.worksheet(sheet_name)

                # Получение существующих ID
                existing_ids = set(worksheet.col_values(1)[1:])

                # Подготовка новых строк
                new_rows = []
                for _, row in excel_df.iterrows():
                    if str(row["ID"]) not in existing_ids:
                        new_rows.append([
                            str(row["ID"]),
                            row["ФИО"],
                            row["Группы"],
                            "", "", "", ""
                        ])
                
                # Добавление новых строк
                if new_rows:
                    worksheet.append_rows(new_rows, value_input_option="RAW")
                    message = f'Добавлено {len(new_rows)} новых учеников.'
                else:
                    message = "Новых учеников для добавления не найдено."

                os.remove(file_path) # Удаляем временный файл

            except Exception as e:
                message = f"Произошла ошибка: {e}"

            form = UploadFileForm()
    else:
        form = UploadFileForm()
    return render(request, 'app_home/add_student.html', {'form': form, 'message': message})