import flask
from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, fresh_login_required, current_user
from flask_cors import CORS, cross_origin
import json
import os
from data_reciever import functions
from werkzeug.security import check_password_hash
import glob


with open('secret/secret.json', 'r') as f:
    secret_data = json.load(f)
app = Flask(__name__)
cors = CORS(app)
app.secret_key = secret_data['secret_key']
app.debug = True
db_user = secret_data['db_user']
db_password = secret_data['db_password']
db_host = secret_data['db_host']
db_port = secret_data['db_port']
db_name = secret_data['db_name']
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
login_manager = LoginManager(app)
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, nullable=False, primary_key=True)
    student_name = db.Column(db.String(50), nullable=False)
    student_login = db.Column(db.String(4), nullable=False)
    student_password = db.Column(db.String(5), nullable=False)

    def get_id(self):
        return self.student_id


@app.route('/')
def main_page():
    return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if current_user.is_authenticated:
        if current_user.student_id == 999:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('student_page', pid=current_user.student_id))
    login = request.form.get('login')
    password = request.form.get('password')
    if login and password:
        user = User.query.filter_by(student_login=login).first()
        if user and (user.student_password == password or check_password_hash(user.student_password, password)):
            login_user(user)
            page_id = user.student_id
            if page_id == 999:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('student_page', pid=page_id))
        else:
            flash('Неверный логин или пароль')
    return render_template('login_page.html')


@app.route('/logout')
def logout_page():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for('login_page'))
    else:
        return redirect(url_for('login_page'))


@app.after_request
def redirect_to_sign_in(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)
    else:
        return response


@app.route('/student/<int:pid>')
@login_required
def student_page(pid):
    if pid == current_user.student_id or current_user.student_id == 999:
        connection, cursor = functions.db_connection()
        cursor.execute('SELECT student_id, student_name FROM students WHERE student_id = %s', (pid,))
        record = cursor.fetchall()[0]
        current_student_id = record[0]
        current_student_name = record[1]
        cursor.execute('SELECT * FROM get_current_homework_progress(%s)', (pid,))
        current_homework_progress = int(cursor.fetchall()[0][0])
        cursor.execute('SELECT * FROM get_current_classwork_progress(%s)', (pid,))
        current_classwork_progress = int(cursor.fetchall()[0][0])
        cursor.execute('SELECT * FROM get_last_homework_score(%s)', (pid,))
        last_homework_progress = int(cursor.fetchall()[0][0])
        cursor.execute('SELECT * FROM get_last_classwork_score(%s)', (pid,))
        last_classwork_progress = int(cursor.fetchall()[0][0])
        cursor.execute('SELECT homework_lvl, classwork_lvl FROM students WHERE student_id = %s', (pid,))
        record = cursor.fetchall()[0]
        homework_lvl = record[0]
        classwork_lvl = record[1]
        cursor.execute("SELECT mana_earned, SUM(mana) FROM students JOIN total_grades ON student_id = fk_student_id JOIN works ON fk_work_id = work_id WHERE is_homework = 'True' AND student_id = %s GROUP BY mana_earned", (pid,))
        mana_tmp = cursor.fetchall()[0]
        mana = mana_tmp[1] - mana_tmp[0]
        data = [current_homework_progress, current_classwork_progress, last_homework_progress, last_classwork_progress, homework_lvl, classwork_lvl, mana, current_student_name, current_student_id]
        cursor.close()
        connection.close()
        return render_template("student.html", data=data)
    else:
        return redirect(url_for('student_page', pid=current_user.student_id))


@app.route('/student')
def student():
    if current_user.student_id != 999:
        return redirect(url_for('student_page', pid=current_user.student_id))
    else:
        return redirect(url_for('admin'))


@app.route('/stats/<int:pid>')
@login_required
def stats_page(pid):
    gid = flask.request.url
    if os.path.isfile(f'static/exam_graph_{pid}.png'):
        os.remove(f'static/exam_graph_{pid}.png')
    if os.path.isfile(f'static/exam_graph_speaking_{pid}.png'):
        os.remove(f'static/exam_graph_speaking_{pid}.png')
    if 'gid' in gid:
        graph_id = int(gid.split('gid=')[1])
    else:
        graph_id = 0
    if pid == current_user.student_id or current_user.student_id == 999:
        connection, cursor = functions.db_connection()
        cursor.execute('SELECT student_name FROM students WHERE student_id = %s', (pid,))
        current_student_name = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM get_current_homework_progress(%s)', (pid,))
        current_student_homework_progress = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM get_current_classwork_progress(%s)', (pid,))
        current_student_classwork_progress = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM get_homeworks_progress_others(%s)', (pid,))
        others_homework_progress = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM get_classworks_progress_others(%s)', (pid,))
        others_classwork_progress = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM comparing_last_homework(%s)', (pid,))
        last_homework_others = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM get_last_homework_score(%s)', (pid,))
        last_homework = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM comparing_last_classwork(%s)', (pid,))
        last_classwork_others = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM get_last_classwork_score(%s)', (pid,))
        last_classwork = cursor.fetchall()[0][0]
        cursor.execute('SELECT * FROM get_themes(%s)', (pid,))
        record = cursor.fetchall()
        themes = []
        for theme in record:
            cur_theme = theme[0][:-3]
            themes.append(cur_theme)
            if os.path.isfile(f'static/all_graphs_{cur_theme}_{pid}.png'):
                os.remove(f'static/all_graphs_{cur_theme}_{pid}.png')
        cursor.execute('SELECT * FROM compare_exams(%s)', (pid,))
        exam_grades = cursor.fetchall()
        exam_grade_needed = 9
        if exam_grades:
            exam = True
        else:
            exam = False
        cursor.execute('SELECT * FROM compare_exams_speaking(%s)', (pid,))
        exam_grades_speaking = cursor.fetchall()
        if exam_grades_speaking:
            exam_speaking = True
        else:
            exam_speaking = False
        cursor.execute("SELECT * FROM compare_themes(%s)", (pid,))
        themes_grades = cursor.fetchall()
        data = [current_student_name, current_student_homework_progress, current_student_classwork_progress, others_homework_progress, others_classwork_progress, last_homework, last_homework_others, last_classwork, last_classwork_others, themes, exam_grades, exam_grade_needed, exam_grades_speaking, themes_grades]
        if graph_id == 1:
            themes_dict = functions.split_grades_themes(themes_grades)
            theme = 'Площадь'
            functions.all_graphs(current_student_name, themes_dict[theme], theme, pid)
        elif graph_id == 2:
            themes_dict = functions.split_grades_themes(themes_grades)
            theme = 'Части'
            functions.all_graphs(current_student_name, themes_dict[theme], theme, pid)
        elif graph_id == 3:
            themes_dict = functions.split_grades_themes(themes_grades)
            theme = 'Движение'
            functions.all_graphs(current_student_name, themes_dict[theme], theme, pid)
        elif graph_id == 4:
            themes_dict = functions.split_grades_themes(themes_grades)
            theme = 'Совместная работа'
            functions.all_graphs(current_student_name, themes_dict[theme], theme, pid)
        elif graph_id == 5:
            themes_dict = functions.split_grades_themes(themes_grades)
            theme = 'Обратный ход'
            functions.all_graphs(current_student_name, themes_dict[theme], theme, pid)
        elif graph_id == 6:
            themes_dict = functions.split_grades_themes(themes_grades)
            theme = 'Головы и ноги'
            functions.all_graphs(current_student_name, themes_dict[theme], theme, pid)
        elif graph_id == 7:
            functions.exam_graph(current_student_name, exam_grades, pid, exam_grade_needed)
        elif graph_id == 8:
            functions.exam_graph_speaking(current_student_name, exam_grades_speaking, pid)
        return render_template("stats_page.html", data=data, pid=pid, gid=graph_id, ex=exam, ex_s=exam_speaking)
    else:
        return redirect(url_for('stats_page', pid=current_user.student_id))


@app.route('/stats/<int:pid>/graph/<int:gid>')
@login_required
def graph_page(pid, gid):
    if pid == current_user.student_id or current_user.student_id == 999:
        return redirect(url_for('stats_page', pid=pid, gid=gid))


@app.route('/stats/<int:pid>/graph')
def graph(pid):
    if current_user.student_id != 999:
        return redirect(url_for('stats_page', pid=pid))
    else:
        return redirect(url_for('admin'))


@app.route('/stats')
def stats():
    if current_user.student_id != 999:
        return redirect(url_for('stats_page', pid=current_user.student_id))
    else:
        return redirect(url_for('admin'))


@app.route('/admin')
@login_required
def admin():
    if current_user.student_id == 999:
        connection, cursor = functions.db_connection()
        cursor.execute('SELECT * FROM waiting_for_mana()')
        waiters_for_mana = cursor.fetchall()
        cursor.execute('SELECT student_id, student_name FROM students WHERE student_id < 999 ORDER BY student_id;')
        added_students = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('admin_page.html', data=waiters_for_mana, students=added_students)
    else:
        return redirect(url_for('student_page', pid=current_user.student_id))


@app.route('/mana_give/<int:pid>')
@login_required
def mana_give(pid):
    if current_user.is_authenticated:
        if current_user.student_id == 999:
            functions.mana_give(pid)
            return redirect('/admin')
        else:
            return redirect('/login')
    else:
        return redirect('/login')


@app.route('/rating')
@login_required
def rating():
    if current_user.is_authenticated:
        current_id = current_user.student_id
        connection, cursor = functions.db_connection()
        cursor.execute("SELECT student_id, student_name, homework_lvl FROM students WHERE student_id < 999 ORDER BY homework_lvl DESC;")
        ratings = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('rating_page.html', data=ratings, current_id=current_id)
    else:
        return redirect('/login')


@app.route('/db_operation/<p_name>')
@login_required
def db_operation(p_name):
    if current_user.is_authenticated:
        if current_user.student_id == 999:
            if p_name == 'update_grades':
                functions.db_update_total_grades()
            elif p_name == 'add_students':
                functions.db_update_students()
            elif p_name == 'restart_students':
                connection, cursor = functions.db_connection()
                cursor.execute('DELETE FROM students WHERE student_id < 999; ALTER SEQUENCE seq_student_id RESTART WITH 1; COMMIT;')
                functions.db_update_students()
                connection.close()
                cursor.close()
            elif p_name == 'update_works':
                functions.db_update_works_info()
            return redirect('/admin')
        else:
            return redirect('/login')
    else:
        return redirect('/login')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


if __name__ == '__main__':
    app.run()
