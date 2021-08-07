from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, fresh_login_required, \
    current_user
import psycopg2
from data_reciever import functions
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "sandr vonyaet kakashkami"
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
        if current_user.status == 0:
            return redirect(url_for('student_page', pid=current_user.student_id))
        else:
            return redirect(url_for('admin'))
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


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout_page():
    logout_user()
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
        '''
        connection, cursor = functions.db_connection()
        cursor.execute('SELECT score FROM total_grades WHERE fk_student_id = %s', (pid,))
        record = cursor.fetchall()
        cursor.close()
        connection.close()
        '''
        return render_template("student.html")#, data=record)
    else:
        return redirect(url_for('student_page', pid=current_user.student_id))


@app.route('/admin')
@login_required
def admin():
    if current_user.student_id == 999:
        return render_template('admin_page.html')
    else:
        return redirect(url_for('student_page', pid=current_user.student_id))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


if __name__ == '__main__':
    app.run()
