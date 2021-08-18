from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, fresh_login_required, \
    current_user
from flask_cors import CORS, cross_origin
import psycopg2
from data_reciever import functions
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
cors = CORS(app)
app.secret_key = "kolya i sandr gei"
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Nickrotay12@localhost:5432/Progressive_math'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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


@app.route('/', methods=['POST', 'GET'])
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
            flash('Login or password is not correct')
    return render_template('login_page.html')


'''
@app.route('/auth', methods=['POST'])
def login_page():
    json_payload = request.get_json()
    user_entry = User.query.filter_by(student_login=json_payload['login']).first()
    if user_entry:
        if check_password_hash(user_entry.student_password, json_payload['password']):
            login_user(user_entry)
            return {"isLoggedIn": current_user.is_authenticated,
                    "user_id": user_entry.student_id}, 200

    return jsonify(authorization=False), 403
'''


@app.route('/logout', methods=['POST', 'GET'])
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
    if pid == 999:
        return redirect(url_for('admin'))
    if pid == current_user.student_id:
        connection, cursor = functions.db_connection()
        cursor.execute('SELECT * FROM get_current_homework_progress(%s)', (current_user.student_id,))
        record = cursor.fetchall()[0]
        current_homework_progress = round(record[0] / record[1] * 100)
        cursor.execute('SELECT * FROM get_current_classwork_progress(%s)', (current_user.student_id,))
        record = cursor.fetchall()[0]
        current_classwork_progress = round(record[0] / record[1] * 100)
        cursor.execute('SELECT * FROM get_last_homework_score(%s)', (current_user.student_id,))
        record = cursor.fetchall()[0]
        last_homework_progress = round(record[0] / record[1] * 100)
        cursor.execute('SELECT * FROM get_last_classwork_score(%s)', (current_user.student_id,))
        record = cursor.fetchall()[0]
        last_classwork_progress = round(record[0] / record[1] * 100)
        cursor.execute('SELECT homework_lvl, classwork_lvl FROM students WHERE student_id = %s', (current_user.student_id,))
        record = cursor.fetchall()[0]
        homework_lvl = record[0]
        classwork_lvl = record[1]
        data = [current_homework_progress, current_classwork_progress, last_homework_progress, last_classwork_progress, homework_lvl, classwork_lvl]
        cursor.close()
        connection.close()
        return render_template("student.html", data=data)
    else:
        return redirect(url_for('student_page', pid=current_user.student_id))


@app.route('/admin')
@login_required
def admin():
    if current_user.student_id == 999:
        connection, cursor = functions.db_connection()
        cursor.execute('SELECT * FROM waiting_for_mana()')
        waiters_for_mana = cursor.fetchall()
        return render_template('admin_page.html', data=waiters_for_mana)
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
                cursor.execute('TRUNCATE TABLE students RESTART IDENTITY CASCADE; COMMIT;')
                functions.admin_creator()
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
