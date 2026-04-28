import sqlite3
from flask import g
import os
import uuid
from flask import send_from_directory
from flask import Flask, render_template, request, redirect, session
#from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "notesphere_secret"

# MySQL Config
'''app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # put your MySQL password if any
app.config['MYSQL_DB'] = 'notesphere

mysql = MySQL(app)'''

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with sqlite3.connect("notesphere.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            filename TEXT,
            category TEXT
        )
        """)

        conn.commit()
        conn.close()


init_db()

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            return redirect('/dashboard')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM files")
    files = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html', files=files)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']

        file = request.files['file']
        filename = file.filename
        file.save(os.path.join("uploads", filename))

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO files (title, description, filename, category)
        VALUES (?, ?, ?, ?)
        """, (title, description, filename, category))

        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template('upload.html')@app.route('/download/<filename>')

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join("uploads", filename), as_attachment=True)


if __name__ == "__main__":
    app.run()
