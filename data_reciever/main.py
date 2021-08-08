# coding: utf-8
from functions import send_email, db_update_works_info, total_info_creator, db_update_students, db_update_total_grades, login_password_creator, db_connection
from service import service_function
from werkzeug.security import generate_password_hash, check_password_hash


if __name__ == '__main__':
    pass
    connection, cursor = db_connection()
    cursor.close()
    connection.close()
    db_update_students()
    #db_update_works_info()
    #db_update_total_grades()
