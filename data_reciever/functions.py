# coding: utf-8
import pandas as pd
from service import service_function
from collections import defaultdict
from random import randint
from transliterate import translit
import time
import psycopg2

SPREADSHEET_ID = '1saZ765b_vW0iGx5GHkvQYvosUhmsTRSorRq8woZ7twM'
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
sheet_names = ['Площадь класс', 'Площадь дз', 'Части класс', 'Части дз',
             'Движение класс', 'Движение дз', 'Совместная класс', 'Совместная дз',
             'Обратный ход класс', 'Обратный ход дз', 'Головы и ноги класс',
             'Головы и ноги дз', 'Экзамен письм класс', 'экзамен домашний(баллы 2007)',
             'Экзамен домашний письм', 'Экзамен устный класс', 'Экзамен устный дз']


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
    return login, password


def db_update_students():
    service = service_function()
    sheet_name = sheet_names[0]
    connection, cursor = db_connection()
    cursor.execute("SELECT student_row FROM students")
    used_rows = cursor.fetchall()
    students_amount = len(service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A4:A40').execute()['values'])
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
        cursor.execute("INSERT INTO students(student_name, student_login, student_password, student_row) VALUES (%s, %s, %s, %s); COMMIT", (student_name, info[0], info[1], row))
    if connection:
        cursor.close()
        connection.close()
    else:
        return 'Не удалось подключиться к базе данных'


def info_creator(sheet_name):
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
    total_student_information = info_creator(sheet_names[0])
    for i in range(1, len(sheet_names)):
        current_sheet_students = info_creator(sheet_names[i])
        for j in range(len(current_sheet_students)):
            total_student_information[j] = total_student_information[j] | current_sheet_students[j]
    return total_student_information


def borders(sheet_name, service):
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
    connection, cursor = db_connection()
    cursor.execute("TRUNCATE TABLE total_grades;")
    cursor.execute("SELECT student_id FROM students;")
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
