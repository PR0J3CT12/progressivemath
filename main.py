# coding: utf-8
from functions import db_update_works_info, db_update_students, db_update_total_grades, db_connection, admin_creator, total_info_creator_test, lvl_update, info_creator
from collections import defaultdict
import time
import pymysql
from werkzeug.security import generate_password_hash
import os.path
import os
import json
from pymysql.constants import CLIENT


if __name__ == '__main__':
    pass
    '''
    x = total_info_creator_test()
    ind = 4
    for i in x:
        print(ind)
        ind+=1
        for j in i:
            print(j, i[j])
        if ind==7:
            break
    '''
    connection, cursor = db_connection()
    cursor.execute("DELETE FROM total_grades WHERE score > -1")
    z = cursor.fetchall()
    if not z:
        print('empty')