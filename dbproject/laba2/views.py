# views.py
import os
import re
import sqlite3  # Використовуйте ваш реляційний двигун, якщо не SQLite
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.apps import apps
from django.templatetags.static import static  # Імпортуємо static

from django.shortcuts import render
from django.apps import apps
from django.http import HttpResponse

def all_records_view(request):
    # Отримуємо всі моделі, які починаються з "laba2_"
    app_models = apps.get_app_config('laba2').get_models()
    
    # Словник для зберігання даних
    tables_data = {}

    for model in app_models:
        if model._meta.db_table.startswith('laba2_'):
            # Отримуємо назву таблиці без префіксу
            table_name = model._meta.db_table[len('laba2'):]

            # Отримуємо всі записи з моделі
            records = model.objects.all()

            # Додаємо назву таблиці та записи до словника
            tables_data[table_name] = records

    # Генеруємо HTML-контент
    html_content = """
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Всі таблиці</title>
            <link rel="stylesheet" type="text/css" href="{css_url}">
        </head>
        <body>
    """.format(css_url=static('laba2/styles.css'))  # Підключаємо CSS

    for table_name, records in tables_data.items():
        # Замінюємо "_" на " " і робимо перші букви великими
        formatted_table_name = table_name.replace('_', ' ').title()
        html_content += f"<h2>Таблиця: {formatted_table_name}</h2>"
        html_content += "<table border='1'><tr>"

        # Отримуємо заголовки стовпців
        columns = [field.name for field in records.model._meta.fields]
        for column in columns:
            formatted_column_name = column.replace('_', ' ').title()  # Форматуємо назву стовпця
            html_content += f"<th>{formatted_column_name}</th>"
        html_content += "</tr>"

        # Виводимо записи
        for record in records:
            html_content += "<tr>"
            for column in columns:
                value = getattr(record, column, 'N/A')  # Отримуємо значення або 'N/A'
                html_content += f"<td>{value}</td>"
            html_content += "</tr>"
        html_content += "</table>"

    html_content += """
        </body>
    </html>
    """
    return HttpResponse(html_content, content_type='text/html')

def upload_sql_file_view(request):
    if request.method == 'POST':
        sql_file = request.FILES.get('sql_file')

        if sql_file:
            # Зберігаємо файл у тимчасовому місці
            temp_file_path = os.path.join(settings.MEDIA_ROOT, sql_file.name)

            # Переконайтесь, що директорія існує
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

            with open(temp_file_path, 'wb+') as destination:
                for chunk in sql_file.chunks():
                    destination.write(chunk)

            # Виконуємо SQL запити
            connection = sqlite3.connect(settings.DATABASES['default']['NAME'])  # Ваша база даних
            cursor = connection.cursor()

            with open(temp_file_path, 'r') as f:
                sql_script = f.read()

                # Додаємо префікс laba2_ до назв таблиць
                sql_script = re.sub(r'\b(DiscountCard|Director|Client|Employee|Warehouse|Supplier|Product|Store|DeliveryService|PickupPoint|Manufacturer|Order)\b', r'laba2_\1', sql_script)

                # Розділяємо запити та обробляємо їх
                for statement in sql_script.split(';'):
                    statement = statement.strip()
                    if statement:  # Перевірка на пусті рядки
                        try:
                            # Замінюємо записи у таблицях
                            if statement.startswith('INSERT INTO'):
                                # Отримуємо назву таблиці
                                table_name = re.search(r'INSERT INTO (.+?) ', statement).group(1).strip()
                                table_name = f"{table_name}"

                                # Видаляємо всі записи з таблиці
                                cursor.execute(f'DELETE FROM {table_name};')

                            cursor.execute(statement)  # Виконуємо запит
                        except sqlite3.OperationalError as e:
                            print(f'Error executing statement: {statement} - {str(e)}')  # Виводимо помилку
                            continue  # Продовжуємо до наступного запиту
                        except sqlite3.IntegrityError as e:
                            print(f'Error executing statement: {statement} - {str(e)}')  # Виводимо помилку при конфлікті

                connection.commit()

            # Видаляємо тимчасовий файл
            os.remove(temp_file_path)
            return HttpResponse('SQL file processed successfully.')

    return render(request, 'laba2/upload_sql.html')

def home_view(request):
    return render(request, 'laba2/home.html')