# coding: utf-8
from collections import defaultdict
from random import randint
from transliterate import translit
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os.path, os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from platform import python_version

SPREADSHEET_ID = '1saZ765b_vW0iGx5GHkvQYvosUhmsTRSorRq8woZ7twM'
sheet_names = ['Площадь класс', 'Площадь дз', 'Части класс', 'Части дз',
             'Движение класс', 'Движение дз', 'Совместная класс', 'Совместная дз',
             'Обратный ход класс', 'Обратный ход дз', 'Головы и ноги класс',
             'Головы и ноги дз', 'Экзамен письм класс', 'экзамен домашний(баллы 2007)',
             'Экзамен домашний письм', 'Экзамен устный класс', 'Экзамен устный дз']


def service_function():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials).spreadsheets().values()
    return service


def send_email(file):
    """
    Send an email
    """
    server = 'smtp.gmail.com'
    user = '7pr0j3ct12@gmail.com'
    password = 'Nickrotay12'
    sender = user
    to_who = 'nik.rotay@gmail.com'
    subject = 'Пароли'
    text = 'Текст'
    file = 'passwords.txt'
    basename = os.path.basename(file)
    filesize = os.path.getsize(file)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'Python script <' + sender + '>'
    msg['To'] = ', '.join(to_who)
    msg['Reply-To'] = sender
    msg['Return-Path'] = sender
    msg['X-Mailer'] = 'Python/' + (python_version())
    part_text = MIMEText(text, 'plain')
    part_file = MIMEBase('application', 'octet-stream; name="{}"'.format(basename))
    part_file.set_payload(open(file, "rb").read())
    part_file.add_header('Content-Description', basename)
    part_file.add_header('Content-Disposition', 'attachment; filename="{}"; size={}'.format(basename, filesize))
    encoders.encode_base64(part_file)
    msg.attach(part_text)
    msg.attach(part_file)
    mail = smtplib.SMTP_SSL(server)
    mail.login(user, password)
    mail.sendmail(sender, to_who, msg.as_string())
    mail.quit()



def db_connection():
    """
    Функция для подключения к базе данных
    Возвращает connection и cursor
    """
    try:
        connection = psycopg2.connect(user="postgres", password="Nickrotay12", host="127.0.0.1", port="5432", dbname="Progressive_math")
        cursor = connection.cursor()
        return connection, cursor
    except:
        return 0, 0


def login_password_creator(name, row):
    """
    Фамилия Имя, строка, в которой ученик находится на вход
    Логин и пароль на выход
    """
    trans = translit(name, 'ru', reversed=True).split()
    if row < 13:
        login = trans[0][0] + trans[1][0] + '0' + str(row - 3)
    else:
        login = trans[0][0] + trans[1][0] + str(row - 3)
    password = str(randint(10000, 99999))
    password_hash = generate_password_hash(password)
    return name, login, password, password_hash


def db_update_students():
    """
    Функция для обновления таблицы students
    """
    if os.path.isfile('passwords.txt'):
        os.remove('passwords.txt')
    service = service_function()
    sheet_name = sheet_names[0]
    connection, cursor = db_connection()
    cursor.execute("SELECT student_row FROM students")
    used_rows = cursor.fetchall()
    students_amount = len(service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A4:A50').execute()['values'])
    jump = False
    for i in range(0, students_amount):
        row = i + 4
        for j in range(len(used_rows)):
            if row in used_rows[j]:
                jump = True
                continue
        if jump:
            jump = False
            continue
        student_name = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A{row}:A{row}').execute()['values'][0][0]
        info = login_password_creator(student_name, row)
        with open('passwords.txt', 'a+') as f:
            f.write(info[0] + ' | ' + info[1] + ' | ' + info[2] + '\n')
        cursor.execute("INSERT INTO students(student_name, student_login, student_password, student_row) VALUES (%s, %s, %s, %s); COMMIT", (student_name, info[1], info[3], row))
    if connection:
        cursor.close()
        connection.close()
        send_email('passwords.txt')

    else:
        return 'Не удалось подключиться к базе данных'


def info_creator(sheet_name):
    """
    На вход название листа
    На выход список формата [{"Классная работа 1": 40, "Классная работа 2": 20, ...}, {...}, ...]
    P.S. список учеников(ученик = словарь с результатами по каждой работе на листе
    """
    connection, cursor = db_connection()
    cursor.execute("SELECT student_id FROM students")
    number_of_students = len(cursor.fetchall())
    cursor.execute("SELECT work_name FROM works WHERE sheet_name = %s", (sheet_name,))
    works_names = cursor.fetchall()
    service = service_function()
    current_sheet_students = []
    data = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A4:ZZ{number_of_students+3}').execute()['values']
    all_borders = borders(sheet_name, service)
    for i in range(len(data)):
        data[i] = data[i][4:]
        for j in range(len(data[i])):
            if data[i][j] == '':
                data[i][j] = 0
            else:
                data[i][j] = int(data[i][j])
    for student in data:
        current_student_dict = defaultdict(list)
        for i in range(len(all_borders)):
            current_student_dict[works_names[i][0]] = sum(student[all_borders[i][0]:all_borders[i][1]])
        current_sheet_students.append(current_student_dict)
    return current_sheet_students


def total_info_creator():
    """
    Функция для объединения всех листов после info_creator
    """
    total_student_information = info_creator(sheet_names[0])
    for i in range(1, len(sheet_names)):
        current_sheet_students = info_creator(sheet_names[i])
        for j in range(len(current_sheet_students)):
            total_student_information[j] = total_student_information[j] | current_sheet_students[j]
    return total_student_information


def borders(sheet_name, service):
    """
    На вход название листа и service
    На выход границы клеток всех работ на листе
    """
    borders_info = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A2:ZZ2').execute()['values'][0][4:]
    borders_info.append('')
    all_borders = []
    left_index = 0
    for i in range(len(borders_info)):
        if borders_info[i] == '∑':
            right_index = i - 1
            current_borders = [left_index, right_index]
            if borders_info[i + 1] == '':
                left_index = i + 2
            else:
                left_index = i + 1
            all_borders.append(current_borders)
    return all_borders


def db_update_works_info():
    """
    Функция для перезаписи таблицы works
    """
    service = service_function()
    connection, cursor = db_connection()
    cursor.execute("TRUNCATE TABLE works RESTART IDENTITY CASCADE;")
    for i in range(len(sheet_names)):
        sheet_name = sheet_names[i]
        full_list = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A1:ZZ3').execute()['values']
        score = full_list[2]
        for_names = list(filter(None, full_list[0][4:]))
        names_list = []
        if 'Мана' in for_names:
            is_homework = True
        else:
            is_homework = False
        for k in range(len(for_names)):
            if for_names[k] != 'Мана':
                names_list.append(for_names[k])
        score.append('')
        works_info = []
        amount = 0
        num = 0
        work_counter = 0
        for c in range(len(score)):
            if score[c] != '':
                amount += int(score[c])
                num += 1
                if int(score[c]) == 0:
                    num -= 1
            if score[c] == '':
                if amount != 0:
                    work_name = names_list[work_counter]
                    works_info.append([work_name, sheet_name, amount, num, is_homework])
                    work_counter += 1
                amount = 0
                num = 0
        for j in range(len(works_info)):
            cursor.execute("INSERT INTO works(work_name, sheet_name, max_score, exercises, is_homework) VALUES (%s, %s, %s, %s, %s); COMMIT", (works_info[j][0], works_info[j][1], works_info[j][2], works_info[j][3], works_info[j][4]))
    return 0


def db_update_total_grades():
    """
    Функция для перезаписи таблицы total_grades
    """
    connection, cursor = db_connection()
    cursor.execute("TRUNCATE TABLE total_grades;")
    cursor.execute("SELECT student_id FROM students WHERE student_id < 999;")
    students = cursor.fetchall()
    results = total_info_creator()
    for student in students:
        current_student_id = student[0]
        cursor.execute("SELECT work_id, work_name FROM works;")
        record = cursor.fetchall()
        current_student_results = results[current_student_id - 1]
        for work in record:
            current_work_name = work[1]
            current_work_id = work[0]
            current_work_grade = current_student_results[current_work_name]
            cursor.execute("INSERT INTO total_grades(fk_student_id, fk_work_id, score) VALUES (%s, %s, %s); COMMIT", (current_student_id, current_work_id, current_work_grade))
