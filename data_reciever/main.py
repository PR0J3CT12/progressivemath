# coding: utf-8
from functions import borders, mana_give, send_email, db_update_works_info, info_creator, total_info_creator, db_update_students, db_update_total_grades, login_password_creator, db_connection
from service import service_function
from werkzeug.security import generate_password_hash, check_password_hash


if __name__ == '__main__':
    pass
    #connection, cursor = db_connection()
    #cursor.execute("SELECT work_id, work_name FROM works;")
    #x = cursor.fetchall()
    #print(x)
    #db_update_students()
    #db_update_works_info()
    db_update_total_grades()
    #results = total_info_creator()
    #for i in range(len(results)):
    #    print(i)
    #    print(results[i])
