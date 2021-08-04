# coding: utf-8
import pandas as pd
from service import service_function
from collections import defaultdict
from random import randint
from transliterate import translit
import time
import psycopg2

SPREADSHEET_ID = '1saZ765b_vW0iGx5GHkvQYvosUhmsTRSorRq8woZ7twM'
service_acc = service_function()
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
        connection = psycopg2.connect(user="postgres", password="Nickrotay12", host="127.0.0.1", port="5432",
                                  dbname="Progressive_math")
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
    if row < 10:
        login = trans[0][0] + trans[1][0] + '0' + str(row - 3)
    else:
        login = trans[0][0] + trans[1][0] + str(row - 3)
    password = str(randint(10000, 99999))
    return login, password


def update_db_students():
    connection, cursor = db_connection()
    cursor.execute("SELECT student_row FROM students")
    used_rows = cursor.fetchall()[0]
    if connection:
        cursor.close()
        connection.close()
    else:
        return 'Не удалось подключиться к базе данных'


def df_creator(range_name, service=service_acc):
    """
    Название листа на вход
    DataFrame на выход
    """
    data = service.get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    df = pd.DataFrame(data['values'])
    return df


def borders(df):
    """
    DataFrame листа на вход
    Список из границ работ в данном листе на выход
    """
    list_for_work_parser = df.loc[1][4:].to_string(index=False).split("\n")
    work_parser = []
    left = 4
    #mana_list = []
    top_string_list = df.loc[0].to_string(index=False).split("\n")
    homework = False
    for i in range(len(top_string_list)):
        if 'Мана' in top_string_list[i]:
            #mana_list.append(i)
            homework = True
            break
    for k in range(len(list_for_work_parser)):
        if '∑' in list_for_work_parser[k]:
            if homework:
                right = k + 4
                work_parser.append([left, right])
                left = k + 6
            else:
                right = k + 4
                work_parser.append([left, right])
                left = k + 5
    return work_parser


def reciever(name, list_name):
    """
    На вход имя студента
    На вход название листа
    На выход словарь формата {"Имя":..., ..., "Домашняя работа №1":..., ...}
    """
    try:
        df = df_creator(list_name)
        df_print = df.to_string(index=False)
        names_list = df[0].to_string(index=False).split("\n")[3:]
        for i in range(len(names_list)):
            x = names_list[i].replace('     ', '')
            if x == name:
                name_id = i
                break
        current_student = df.loc[name_id + 3].to_string(index=False).split("\n")
        for i in range(1, len(current_student)):
            x = current_student[i].replace(' ', '')
            x = x.replace(',', '.')
            if x == '':
                x = '0'
            current_student[i] = x
        borders_list = borders(df)
        student = defaultdict(list)
        #student['Имя и фамилия'] = current_student[0]
        #student['Сумма баллов'] = current_student[1]
        #student['Процент выполненной работы'] = current_student[2]
        #student['Уровень'] = current_student[3]
        for i in range(len(borders_list)):
            student[str(df.loc[0][borders_list[i][0]])] = current_student[borders_list[i][0]:borders_list[i][1]]
        return student
    except:
        return 'Ученик не найден!'


def total_reciever(name):
    total_dict = defaultdict(list)
    for i in range(len(sheet_names)):
        current_dict = reciever(name, sheet_names[i])
        #print(type(total_dict), type(current_dict))
        total_dict = total_dict | current_dict
    return total_dict


def db_update_works_info():
    service = service_function()
    for i in range(len(sheet_names)):
        sheet_name = sheet_names[i]
        connection, cursor = db_connection()
        full_list = service.get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!A1:CZ3').execute()['values']
        score = full_list[2]
        for_names = list(filter(None, full_list[0][4:]))
        names_list = []
        if 'Мана' in for_names:
            is_homework = True
        else:
            is_homework = False
        for i in range(len(for_names)):
            if for_names[i] != 'Мана':
                names_list.append(for_names[i])
        score.append('')
        works_info = []
        amount = 0
        num = 0
        work_counter = 0
        for i in range(len(score)):
            if score[i] != '':
                amount += int(score[i])
                num += 1
            if score[i] == '':
                if amount != 0:
                    work_name = names_list[work_counter]
                    works_info.append([work_name, sheet_name, amount, num, is_homework])
                    work_counter += 1
                amount = 0
                num = 0
        for i in range(len(works_info)):
            cursor.execute("INSERT INTO works(work_name, sheet_name, max_score, exercises, is_homework) VALUES (%s, %s, %s, %s, %s); COMMIT", (works_info[i][0], works_info[i][1], works_info[i][2], works_info[i][3], works_info[i][4]))
        return works_info