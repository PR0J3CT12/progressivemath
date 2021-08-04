# coding: utf-8
from functions import reciever, login_password_creator, db_connection
import time
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from contextlib import closing
from service import service_function
from transliterate import translit


if __name__ == '__main__':
    pass
    connection = False
    #connection = psycopg2.connect(user="postgres", password="Nickrotay12", host="127.0.0.1", port="5432", dbname="Progressive_math")
    #cursor = connection.cursor()
    connection, cursor = db_connection()
    service = service_function()
    result = service.get(spreadsheetId='1saZ765b_vW0iGx5GHkvQYvosUhmsTRSorRq8woZ7twM', range='Площадь дз!A4').execute()['values'][0][0]
    row = 4
    info = login_password_creator(result, row)
    cursor.execute("INSERT INTO students(student_name, student_login, student_password, student_row) VALUES (%s, %s, %s, %s)", (result, info[0], info[1], row))
    cursor.execute("COMMIT")
    cursor.execute("SELECT * FROM students")
    record = cursor.fetchall()
    print(record)
    if connection:
        cursor.close()
        connection.close()
    '''
    student_name = 'Пупкин Василий'
    list_name = 'Площадь дз'
    lists = ['Площадь класс', 'Площадь дз', 'Части класс', 'Части дз',
             'Движение класс', 'Движение дз', 'Совместная класс', 'Совместная дз',
             'Обратный ход класс', 'Обратный ход дз', 'Головы и ноги класс',
             'Головы и ноги дз', 'Экзамен письм класс', 'экзамен домашний(баллы 2007)',
             'Экзамен домашний письм', 'Экзамен устный класс', 'Экзамен устный дз']
    for i in range(len(lists)):
        #start = time.time()
        print(lists[i])
        x = reciever(student_name, lists[i])
        #stop = time.time() - start
        #print('Time:', stop, ' | ', x)
        print(x)
    '''
