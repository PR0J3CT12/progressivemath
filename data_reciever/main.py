# coding: utf-8
from functions import reciever, login_password_creator, db_connection, sheet_names, db_update_works_info, total_reciever
from service import service_function
import json


if __name__ == '__main__':
    pass



    connection, cursor = db_connection()
    service = service_function()
    student_name = service.get(spreadsheetId='1saZ765b_vW0iGx5GHkvQYvosUhmsTRSorRq8woZ7twM', range='Площадь дз!A4:A40').execute()['values'][0][0]
    #row = 4
    #info = login_password_creator(student_name, row)
    #cursor.execute("INSERT INTO students(student_name, student_login, student_password, student_row) VALUES (%s, %s, %s, %s); COMMIT", (student_name, info[0], info[1], row))
    #cursor.execute("SELECT * FROM students")
    #cursor.execute("SELECT student_row FROM students")
    #record = cursor.fetchall()
    #print(student_name[0])
    #x = db_update_works('Площадь дз', service)
    #score = service.get(spreadsheetId='1saZ765b_vW0iGx5GHkvQYvosUhmsTRSorRq8woZ7twM', range='Площадь дз!A1:CZ3').execute()['values']
    print(total_reciever(student_name))
    if connection:
        cursor.close()
        connection.close()
    '''
    for i in range(len(sheet_names)):
        print(sheet_names[i])
        x = reciever(student_name, sheet_names[i])
        print(x)
    '''