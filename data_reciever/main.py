# coding: utf-8
from functions import borders, mana_give, send_email, db_update_works_info, info_creator, total_info_creator, db_update_students, db_update_total_grades, login_password_creator, db_connection
from service import service_function
from werkzeug.security import generate_password_hash, check_password_hash


if __name__ == '__main__':
    pass
    #total_info_creator()
    connection, cursor = db_connection()
    hash_my = generate_password_hash('123')
    cursor.execute("INSERT INTO students VALUES (%s, %s, %s, %s); COMMIT;", (999, 'admin', 'admin', hash_my))
    cursor.close()
    connection.close()
    #db_update_students()
    #send_email('passwords.txt')
    #db_update_works_info()
    #db_update_total_grades()
