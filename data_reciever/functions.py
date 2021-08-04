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


def db_connection():
    connection = psycopg2.connect(user="postgres", password="Nickrotay12", host="127.0.0.1", port="5432",
                                  dbname="Progressive_math")
    cursor = connection.cursor()
    return connection, cursor


def login_password_creator(name, row):
    trans = translit(name, 'ru', reversed=True).split()
    login = trans[0][0] + trans[1][0] + str(row - 3)
    password = str(randint(10000, 99999))
    return login, password


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
        #st = time.time()
        df = df_creator(list_name)
        #st_ = time.time()
        #print('df_creator time:', st_ - st)
        df_print = df.to_string(index=False)
        names_list = df[0].to_string(index=False).split("\n")[3:]
        #print(names_list)
        #print(df_print)
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
        student['Имя и фамилия'] = current_student[0]
        student['Сумма баллов'] = current_student[1]
        student['Процент выполненной работы'] = current_student[2]
        student['Уровень'] = current_student[3]
        for i in range(len(borders_list)):
            student[str(df.loc[0][borders_list[i][0]])] = current_student[borders_list[i][0]:borders_list[i][1]]
        return student
    except:
        return 'Ученик не найден!'
