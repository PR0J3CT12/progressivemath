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
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5432/progressive_math'
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
        return render_template("student.html")
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
