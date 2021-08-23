# coding: utf-8
from functions import db_update_works_info, db_update_students, db_update_total_grades, db_connection, admin_creator
import json


if __name__ == '__main__':
    pass
    connection, cursor = db_connection()
    cursor.execute('SELECT * FROM get_themes(%s)', (1,))
    record = cursor.fetchall()
    themes = []
    for theme in record:
        themes.append(theme[0][:-3])
    print(themes)
    #admin_creator()
    #db_update_students()
    #db_update_works_info()
    #db_update_total_grades()
