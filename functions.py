# -*- coding: utf-8 -*-
from collections import defaultdict
from random import randint
from transliterate import translit
from werkzeug.security import generate_password_hash
import os.path
import os
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import threading
import time
import pymysql
from pymysql.constants import CLIENT


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, 'total_info.json')
SECRET_FILE = os.path.join(BASE_DIR, 'secret/secret.json')
with open(SECRET_FILE, 'r') as f:
    secret_data = json.load(f)
db_user = secret_data['db_user']
db_password = secret_data['db_password']
db_host = secret_data['db_host']
db_port = secret_data['db_port']
db_name = secret_data['db_name']
PASSWORDS_FILE = os.path.join(BASE_DIR, 'secret/passwords.txt')
STATIC_DIR = os.path.join(BASE_DIR, 'static/')
FONT = os.path.join(STATIC_DIR, 'font.ttf')
#SPREADSHEET_ID = '1QMzDbyOHjA1qW1WrH99pIRuuvR7IFyrPifAbQXWUMb4'
SPREADSHEET_ID = '1saZ765b_vW0iGx5GHkvQYvosUhmsTRSorRq8woZ7twM'
sheet_names = ['Площадь класс', 'Площадь дз', 'Части класс', 'Части дз',
               'Движение класс', 'Движение дз', 'Совместная работа класс', 'Совместная работа дз',
               'Обратный ход класс', 'Обратный ход дз', 'Головы и ноги класс',
               'Головы и ноги дз', 'Экзамен письм класс', 'Экзамен письм дз(баллы 2007)',
               'Экзамен письм дз', 'Экзамен устный класс', 'Экзамен устный дз']


def service_function():
    """
    Функция для работы с Google sheet API
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'secret/credentials.json')
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials).spreadsheets().values()
    return service


def send_email(file):
    """
    Функция для отправки файла с паролями
    На вход файл с паролями
    """
    server = 'smtp.gmail.com'
    user = 'progressive.mail.sender@gmail.com'
    password = secret_data['mail_password']
    sender = user
    to_who = 'nik.rotay@gmail.com'
    subject = 'Пароли'
    text = 'Логины и пароли добавленных пользователей'
    basename = os.path.basename(file)
    filesize = os.path.getsize(file)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'Курсы прогрессивной математики <' + sender + '>'
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
        connection = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name, client_flag=CLIENT.MULTI_STATEMENTS)#, cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()
        return connection, cursor
    except:
        raise Exception('Cant connect to db')


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


def admin_creator():
    """
    Функция для создания админки
    """
    connection, cursor = db_connection()
    hash_my = generate_password_hash(secret_data["admin_password"])
    cursor.execute("INSERT INTO students(student_id, student_name, student_login, student_password) VALUES(%s, %s, %s, %s)", (0, 'admin', 'admin', hash_my))
    connection.commit()
    if connection:
        cursor.close()
        connection.close()


def db_update_students():
    """
    Функция для обновления таблицы students
    """
    if os.path.isfile(PASSWORDS_FILE):
        os.remove(PASSWORDS_FILE)
    service = service_function()
    sheet_name = sheet_names[0]
    connection, cursor = db_connection()
    cursor.execute("SELECT student_id, student_row FROM students WHERE student_id > 1")
    rec = cursor.fetchall()
    used_rows = []
    used_ids = []
    print(rec)
    for i in rec:
        used_ids.append(i[0])
        used_rows.append(i[1])
    if used_ids:
        last_id = max(used_ids) + 1
    else:
        last_id = 1
    print(last_id)
    cursor.execute('ALTER TABLE students AUTO_INCREMENT = %s', last_id)
    cursor.execute("SELECT * FROM students WHERE student_id=1;")
    admin_tmp = cursor.fetchall()
    if len(admin_tmp) == 0:
        admin_creator()
    students_amount = len(service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A4:A50').execute()['values'])
    jump = False
    values = ()
    for i in range(0, students_amount):
        row = i + 4
        for j in range(len(used_rows)):
            if row in used_rows:
                jump = True
                continue
        if jump:
            jump = False
            continue
        student_name = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A{row}:A{row}').execute()['values'][0][0]
        info = login_password_creator(student_name, row)
        string = info[0] + u' | ' + info[1] + u' | ' + info[2] + u'\n'
        with open(PASSWORDS_FILE, 'a+', encoding='utf-8') as ff:
            ff.write(string)
        current_tuple = (student_name, info[1], info[3], row)
        values += current_tuple
    execute_tmp = ''
    execute_string = "INSERT INTO students(student_name, student_login, student_password, student_row) VALUES"
    execute_string_perc = "(%s, %s, %s, %s)"
    for j in range(len(values)//4 - 1):
        execute_tmp += execute_string_perc + ', '
    execute_tmp += execute_string_perc
    execute_string += execute_tmp
    if values:
        cursor.execute(execute_string, values)
        connection.commit()
    if connection:
        cursor.close()
        connection.close()
        if os.path.isfile(PASSWORDS_FILE):
            with open(PASSWORDS_FILE, 'r', encoding='utf-8') as ff:
                x = ff.readlines()
                if len(x) != 0:
                    send_email(PASSWORDS_FILE)
    else:
        raise Exception('Cant connect to db')


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
    data = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A4:ZZ{number_of_students + 3}').execute()['values']
    all_borders, is_homework_list = borders(sheet_name)
    for i in range(len(data)):
        data[i] = data[i][4:]
        for j in range(len(data[i])):
            if ',' in data[i][j]:
                data[i][j] = data[i][j].replace(',', '.')
            if data[i][j] == '' or '-':
                pass
            else:
                data[i][j] = float(data[i][j])
    for student in data:
        is_last_classwork = False
        is_last_homework = False
        current_student_dict = {}
        for i in range(len(all_borders)):
            list_of_grades = student[all_borders[i][0]:all_borders[i][1] + 1]
            cur_string = ''
            for el in list_of_grades:
                cur_string += str(el)
            if len(cur_string) != 0:
                if is_homework_list is True:
                    is_last_homework = works_names[i][0]
                else:
                    is_last_classwork = works_names[i][0]
            current_student_dict[works_names[i][0]] = list_of_grades
        if is_last_homework:
            current_student_dict['Последняя домашняя работа'] = is_last_homework
        if is_last_classwork:
            current_student_dict['Последняя классная работа'] = is_last_classwork
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
            total_student_information[j] = {**total_student_information[j], **current_sheet_students[j]}
    for el in total_student_information:
        if 'Последняя классная работа' not in el:
            el['Последняя классная работа'] = 'Классная работа №1'
        if 'Последняя домашняя работа' not in el:
            el['Последняя домашняя работа'] = 'Домашнее задание №1'
    data = total_student_information[:-1]
    with open(SAVE_DIR, "w") as file:
        json.dump(data, file)
    return total_student_information[:-1]


def total_info_creator_test():
    """
    Функция для объединения всех листов после info_creator | TEST!!!
    """
    total_student_information = info_creator(sheet_names[0])
    for i in range(1, len(sheet_names)):
        current_sheet_students = info_creator(sheet_names[i])
        for j in range(len(current_sheet_students)):
            total_student_information[j] = {**total_student_information[j], **current_sheet_students[j]}
    for el in total_student_information:
        if 'Последняя классная работа' not in el:
            el['Последняя классная работа'] = 'Классная работа №1'
        if 'Последняя домашняя работа' not in el:
            el['Последняя домашняя работа'] = 'Домашнее задание №1'
    data = total_student_information[:-1]
    return total_student_information[:-1]


def borders(sheet_name):
    """
    На вход название листа и service
    На выход границы клеток всех работ на листе
    """
    service = service_function()
    borders_info = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A2:ZZ2').execute()['values'][0][4:]
    borders_info.append('')
    all_borders = []
    left_index = 0
    is_homework_list = False
    for i in range(len(borders_info)):
        if borders_info[i] == '∑':
            right_index = i - 1
            current_borders = [left_index, right_index]
            if borders_info[i] == '∑' and borders_info[i + 1] == '':
                if i + 1 < len(borders_info) - 1:
                    is_homework_list = True
            if borders_info[i + 1] == '':
                left_index = i + 2
            else:
                left_index = i + 1
            all_borders.append(current_borders)
    return all_borders, is_homework_list


def db_update_works_info():
    """
    Функция для перезаписи таблицы works
    """
    start = time.time()
    service = service_function()
    connection, cursor = db_connection()
    cursor.execute("DELETE FROM works WHERE work_id >= 1")
    cursor.execute('ALTER TABLE works AUTO_INCREMENT = 1')
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
        score = score[4:]
        works_info = []
        all_borders = borders(sheet_name)[0]
        for j in range(len(all_borders)):
            current_work = score[all_borders[j][0]:all_borders[j][1]+1]
            to_string = current_work[0]
            for h in range(1, len(current_work)):
                to_string += ' ' + current_work[h]
            work_name = names_list[j]
            works_info.append([work_name, sheet_name, to_string, is_homework])
        for j in range(len(works_info)):
            cursor.execute("INSERT INTO works(work_name, sheet_name, grades_string, is_homework) VALUES (%s, %s, %s, %s)", (works_info[j][0], works_info[j][1], works_info[j][2], int(works_info[j][3])))
            connection.commit()
    if connection:
        cursor.close()
        connection.close()


def mana_give_function(student_id):
    """
    Функция для выдачи маны ученику с id = student_id
    На вход student_id
    """
    connection, cursor = db_connection()
    cursor.execute("SELECT SUM(mana) FROM total_grades RIGHT JOIN works ON work_id = fk_work_id WHERE fk_student_id = %s AND is_homework = 'True';", (student_id,))
    mana = cursor.fetchall()[0][0]
    cursor.execute("UPDATE students SET mana_earned = %s WHERE student_id = %s;", (mana, student_id))
    connection.commit()
    if connection:
        cursor.close()
        connection.close()


def lvl_update(student_id):
    """
    Функция для обновления уровней студента с id = student_id
    На вход student_id
    """
    connection, cursor = db_connection()
    cursor.execute('CALL `get_sum_homeworks_score`(%s, @p1, @p2); SELECT @p1 AS `current_max_score`, @p2 AS `current_score`', student_id)
    homeworks_score = cursor.fetchall()[0]
    homeworks_sum = int(homeworks_score[1] / homeworks_score[0] * 100)
    if homeworks_sum < 10:
        homework_lvl = 1
    elif 10 <= homeworks_sum < 20:
        homework_lvl = 2
    elif 20 <= homeworks_sum < 30:
        homework_lvl = 3
    elif 30 <= homeworks_sum < 40:
        homework_lvl = 4
    elif 40 <= homeworks_sum < 50:
        homework_lvl = 5
    elif 50 <= homeworks_sum < 60:
        homework_lvl = 6
    elif 60 <= homeworks_sum < 70:
        homework_lvl = 7
    elif 70 <= homeworks_sum < 80:
        homework_lvl = 8
    elif 80 <= homeworks_sum < 90:
        homework_lvl = 9
    else:
        homework_lvl = 10
    cursor.execute("UPDATE students SET homework_lvl = %s WHERE student_id = %s;", (homework_lvl, student_id))
    connection.commit()
    if connection:
        cursor.close()
        connection.close()


def db_update_total_grades():
    """
    Функция для перезаписи таблицы total_grades
    """
    print('db start:', threading.currentThread().name)
    start = time.time()
    connection, cursor = db_connection()
    cursor.execute("DELETE FROM total_grades WHERE score > -1")
    connection.commit()
    cursor.execute("SELECT student_id, student_row FROM students WHERE student_id > 1;")
    students = cursor.fetchall()
    start_2 = time.time()
    #results = total_info_creator()
    with open(SAVE_DIR, "r") as file:
        results = json.load(file)
        api = time.time() - start_2
        #print('API:', api)
        cursor.execute("SELECT work_id, work_name FROM works;")
        record = cursor.fetchall()
        cursor.execute("SELECT grades_string FROM works;")
        grades_strings = cursor.fetchall()
        values = ()
        for student in students:
            current_student_id = student[0]
            current_student_row = student[1]
            current_student_results = results[current_student_row - 4]
            for work in record:
                current_work_name = work[1]
                current_work_id = work[0]
                current_last_homework = current_student_results['Последняя домашняя работа']
                current_last_classwork = current_student_results['Последняя классная работа']
                cursor.execute("SELECT work_id FROM works WHERE work_name = %s", (current_last_homework,))
                current_last_homework_id = cursor.fetchall()[0][0]
                cursor.execute("SELECT work_id FROM works WHERE work_name = %s", (current_last_classwork,))
                current_last_classwork_id = cursor.fetchall()[0][0]
                cursor.execute("UPDATE students SET last_homework_id = %s WHERE student_id = %s;", (current_last_homework_id, current_student_id))
                connection.commit()
                cursor.execute("UPDATE students SET last_classwork_id = %s WHERE student_id = %s;", (current_last_classwork_id, current_student_id))
                connection.commit()
                current_work_grades_list = current_student_results[current_work_name]
                current_work_grade_string = grades_strings[current_work_id - 1][0].split(' ')
                current_work_grade = 0
                current_exercises = 0
                current_max_score = 0
                for j in current_work_grade_string:
                    if float(j) == 0:
                        current_exercises += 0
                        current_max_score += 0
                    else:
                        current_exercises += 1
                        current_max_score += float(j)
                for i in range(len(current_work_grades_list)):
                    if current_work_grades_list[i] == '':
                        current_work_grade += 0
                    elif current_work_grades_list[i] == '-':
                        current_max_score -= float(current_work_grade_string[i])
                        current_exercises -= 1
                    else:
                        current_work_grade += float(current_work_grades_list[i])
                current_tuple = (current_student_id, current_work_id, current_work_grade, current_max_score, current_exercises)
                values += current_tuple
        execute_tmp = ''
        execute_string = "INSERT INTO total_grades(fk_student_id, fk_work_id, score, max_score, exercises) VALUES"
        execute_string_perc = "(%s, %s, %s, %s, %s)"
        tries = len(record) * len(students)
        for j in range(tries - 1):
            execute_tmp += execute_string_perc + ', '
        execute_tmp += execute_string_perc + '; '
        execute_string += execute_tmp
        if values:
            cursor.execute(execute_string, values)
            connection.commit()
        for student in students:
            current_student_id = student[0]
            for work in record:
                current_work_id = work[0]
                cursor.execute("CALL `get_current_homework_score`(%s, %s, @p2); SELECT @p2 AS `perc`;", (current_student_id, current_work_id))
                tmp_var = cursor.fetchall()[0][0]
                if tmp_var is not None:
                    percentage = int(tmp_var)
                    if 0 < percentage <= 25:
                        mana = 1
                    elif 25 < percentage <= 50:
                        mana = 2
                    elif 50 < percentage <= 75:
                        mana = 3
                    elif 75 < percentage <= 100:
                        mana = 4
                    else:
                        mana = 0
                    cursor.execute("UPDATE total_grades SET mana = %s WHERE fk_student_id = %s AND fk_work_id = %s;", (mana, current_student_id, current_work_id))
                    connection.commit()
        connection.commit()
        for student in students:
            current_student_id = student[0]
            lvl_update(current_student_id)
        if connection:
            cursor.close()
            connection.close()
        print('2:', time.time() - start - api)
        print('db end:', time.time() - start)


def split_grades_themes(themes_grades_list):
    grades = defaultdict(list)
    for work in themes_grades_list:
        grade = work[1], work[2]
        grades[work[0]] += [grade]
    return grades


if __name__ == '__main__':
    pass
    #scheduler.start()
