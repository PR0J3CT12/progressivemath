# coding: utf-8
from functions import mana_give, send_email, db_update_works_info, total_info_creator, db_update_students, db_update_total_grades, login_password_creator, db_connection
from service import service_function
from werkzeug.security import generate_password_hash, check_password_hash


if __name__ == '__main__':
    pass
    connection, cursor = db_connection()
    #cursor.execute("SELECT * FROM get_current_homework_score(%s, %s)", (1, 5))
    #tmp_var = cursor.fetchall()[0]
    #percentage = int(tmp_var[1] / tmp_var[0] * 100)
    #print(perc)
    cursor.close()
    connection.close()
    #db_update_students()
    #db_update_works_info()
    #db_update_total_grades()
