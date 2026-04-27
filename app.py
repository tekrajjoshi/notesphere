import os
import uuid
from flask import send_from_directory
from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "notesphere_secret"

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # put your MySQL password if any
app.config['MYSQL_DB'] = 'notesphere'

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
                    (username, email, password))
        mysql.connection.commit()
        cur.close()

        return redirect('/login')

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):
            session['user'] = user[1]
            return redirect('/dashboard')

    return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    search = request.args.get('search')

    cur = mysql.connection.cursor()

    if search:
        cur.execute("SELECT * FROM files WHERE title LIKE %s", ("%" + search + "%",))
    else:
        cur.execute("SELECT * FROM files ORDER BY uploaded_at DESC")

    files = cur.fetchall()
    cur.close()

    return render_template("dashboard.html", files=files)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')
    if session['user'] != 'admin':
        return "Access Denied"

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        file = request.files['file']

        if file:
            unique_name = str(uuid.uuid4()) + "_" + file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(filepath)

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO files(title, description, filename, category) VALUES(%s,%s,%s,%s)",
            (title, description, unique_name, category))
            mysql.connection.commit()
            cur.close()

            return redirect('/dashboard')

    return render_template('upload.html')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
