from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///progressive_math.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '<Student %r>' % self.student_id


@app.route('/', methods=['POST', 'GET'])
def main_page():
    if request.method == "POST":
        login = request.form['student_login']
        password = request.form['student_password']
        #print(login, password)
        return 'ok'
    else:
        return render_template("main_page.html")


@app.route('/student/<int:student_id>')
#@login_required
def student(student_id):
    return render_template("student.html")


if __name__ == '__main__':
    app.run()
