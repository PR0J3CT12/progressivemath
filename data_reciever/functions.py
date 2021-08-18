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

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BlockingScheduler()

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
    text = 'Логины и пароли добавленных пользователей'
    file = 'passwords.txt'
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
        connection = psycopg2.connect(user="postgres", password="Nickrotay12", host="127.0.0.1", port="5432", dbname="Progressive_math")
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
    connection, cursor = db_connection()
    hash_my = generate_password_hash('123')
    cursor.execute("INSERT INTO students VALUES (%s, %s, %s, %s); COMMIT;", (999, 'admin', 'admin', hash_my))


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
        cursor.execute(
            "INSERT INTO students(student_name, student_login, student_password, student_row) VALUES (%s, %s, %s, %s); COMMIT",
            (student_name, info[1], info[3], row))
    cursor.execute("SELECT * FROM students WHERE student_id=999;")
    admin_tmp = cursor.fetchall()
    if len(admin_tmp) == 0:
        admin_creator()
    if connection:
        cursor.close()
        connection.close()
        if os.path.isfile('passwords.txt'):
            with open('passwords.txt', 'r') as f:
                x = f.readlines()
                if len(x) != 0:
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
    cursor.execute("SELECT student_id FROM students WHERE student_id<999")
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
            if data[i][j] == '' or '-':
                pass
            else:
                data[i][j] = int(data[i][j])
    is_last_classwork = False
    is_last_homework = False
    for student in data:
        is_last_classwork = False
        is_last_homework = False
        is_last_work = False
        current_student_dict = defaultdict(list)
        for i in range(len(all_borders)):
            list_of_grades = student[all_borders[i][0]:all_borders[i][1] + 1]
            cur_string = ''
            for el in list_of_grades:
                cur_string += str(el)
            if len(cur_string) != 0:
                if is_homework_list is True:
                    is_last_homework = works_names[i][0]
                    is_last_work = True
                else:
                    is_last_classwork = works_names[i][0]
                    is_last_work = True
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
            total_student_information[j] = total_student_information[j] | current_sheet_students[j]
    for j in total_student_information:
        if not j['Последняя домашняя работа']:
            j['Последняя домашняя работа'] = 'Домашнее задание №1'
        if not j['Последняя классная работа']:
            j['Последняя классная работа'] = 'Классная работа №1'
    return total_student_information


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
            cursor.execute("INSERT INTO works(work_name, sheet_name, grades_string, is_homework) VALUES (%s, %s, %s, %s); COMMIT", (works_info[j][0], works_info[j][1], works_info[j][2], works_info[j][3]))


def mana_give(student_id):
    connection, cursor = db_connection()
    cursor.execute("SELECT SUM(mana) FROM total_grades RIGHT JOIN works ON work_id = fk_work_id WHERE fk_student_id = %s AND is_homework = 'True';", (student_id,))
    mana = cursor.fetchall()[0][0]
    cursor.execute("UPDATE students SET mana_earned = %s WHERE student_id = %s; COMMIT;", (mana, student_id))


def lvl_update(student_id):
    connection, cursor = db_connection()
    cursor.execute('SELECT current_score FROM get_sum_classworks_score(%s)', (student_id,))
    classworks_sum = cursor.fetchall()[0][0]
    cursor.execute('SELECT current_score FROM get_sum_homeworks_score(%s)', (student_id,))
    homeworks_sum = cursor.fetchall()[0][0]
    if classworks_sum < 50:
        classwork_lvl = 1
    elif 50 <= classworks_sum < 110:
        classwork_lvl = 2
    elif 110 <= classworks_sum < 180:
        classwork_lvl = 3
    elif 180 <= classworks_sum < 260:
        classwork_lvl = 4
    elif 260 <= classworks_sum < 350:
        classwork_lvl = 5
    elif 350 <= classworks_sum < 450:
        classwork_lvl = 6
    elif 450 <= classworks_sum < 560:
        classwork_lvl = 7
    elif 560 <= classworks_sum < 680:
        classwork_lvl = 8
    elif 680 <= classworks_sum < 810:
        classwork_lvl = 9
    elif 810 <= classworks_sum < 950:
        classwork_lvl = 10
    elif 950 <= classworks_sum < 1100:
        classwork_lvl = 11
    else:
        classwork_lvl = 12
    if homeworks_sum < 50:
        homework_lvl = 1
    elif 50 <= homeworks_sum < 110:
        homework_lvl = 2
    elif 110 <= homeworks_sum < 180:
        homework_lvl = 3
    elif 180 <= homeworks_sum < 260:
        homework_lvl = 4
    elif 260 <= homeworks_sum < 350:
        homework_lvl = 5
    elif 350 <= homeworks_sum < 450:
        homework_lvl = 6
    elif 450 <= homeworks_sum < 560:
        homework_lvl = 7
    elif 560 <= homeworks_sum < 680:
        homework_lvl = 8
    elif 680 <= homeworks_sum < 810:
        homework_lvl = 9
    elif 810 <= homeworks_sum < 950:
        homework_lvl = 10
    elif 950 <= homeworks_sum < 1100:
        homework_lvl = 11
    else:
        homework_lvl = 12
    cursor.execute("UPDATE students SET homework_lvl = %s WHERE student_id = %s; COMMIT;", (homework_lvl, student_id))
    cursor.execute("UPDATE students SET classwork_lvl = %s WHERE student_id = %s; COMMIT;", (classwork_lvl, student_id))


@scheduler.scheduled_job(IntervalTrigger(minutes=3))
def db_update_total_grades():
    """
    Функция для перезаписи таблицы total_grades
    """
    connection, cursor = db_connection()
    cursor.execute("TRUNCATE TABLE total_grades;")
    cursor.execute("SELECT student_id, student_row FROM students WHERE student_id < 999;")
    students = cursor.fetchall()
    results = total_info_creator()
    for student in students:
        current_student_id = student[0]
        current_student_row = student[1]
        cursor.execute("SELECT work_id, work_name FROM works;")
        record = cursor.fetchall()
        current_student_results = results[current_student_row - 4]
        for work in record:
            current_work_name = work[1]
            current_work_id = work[0]
            current_last_homework = current_student_results['Последняя домашняя работа']
            cursor.execute("SELECT work_id FROM works WHERE work_name = %s", (current_last_homework,))
            current_last_homework_id = cursor.fetchall()[0][0]
            cursor.execute("UPDATE students SET last_homework_id = %s WHERE student_id = %s; COMMIT;", (current_last_homework_id, current_student_id))
            current_last_classwork = current_student_results['Последняя классная работа']
            cursor.execute("SELECT work_id FROM works WHERE work_name = %s", (current_last_classwork,))
            current_last_classwork_id = cursor.fetchall()[0][0]
            cursor.execute("UPDATE students SET last_classwork_id = %s WHERE student_id = %s; COMMIT;", (current_last_classwork_id, current_student_id))
            current_work_grades_list = current_student_results[current_work_name]
            cursor.execute("SELECT grades_string FROM works;")
            grades_strings = cursor.fetchall()
            current_work_grade_string = grades_strings[current_work_id - 1][0].split(' ')
            current_work_grade = 0
            current_exercises = 0
            current_max_score = 0
            for j in current_work_grade_string:
                if int(j) == 0:
                    current_exercises += 0
                    current_max_score += 0
                else:
                    current_exercises += 1
                    current_max_score += int(j)
            for i in range(len(current_work_grades_list)):
                if current_work_grades_list[i] == '':
                    current_work_grade += 0
                elif current_work_grades_list[i] == '-':
                    current_max_score -= int(current_work_grade_string[i])
                    current_exercises -= 1
                else:
                    current_work_grade += int(current_work_grades_list[i])
            cursor.execute("INSERT INTO total_grades(fk_student_id, fk_work_id, score, max_score, exercises) VALUES (%s, %s, %s, %s, %s); COMMIT", (current_student_id, current_work_id, current_work_grade, current_max_score, current_exercises))
            cursor.execute("SELECT * FROM get_current_homework_score(%s, %s)", (current_student_id, current_work_id))
            tmp_var = cursor.fetchall()[0]
            if tmp_var[0] is not None and tmp_var[1] is not None:
                percentage = int(tmp_var[1] / tmp_var[0] * 100)
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
                cursor.execute("UPDATE total_grades SET mana = %s WHERE fk_student_id = %s AND fk_work_id = %s; COMMIT;", (mana, current_student_id, current_work_id))
        lvl_update(current_student_id)


if __name__ == '__main__':
    scheduler.start()
