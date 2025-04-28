from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey' #temporary key

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

def initdb():
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('''
                CREATE TABLE IF NOT EXISTS jokes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    rating REAL DEFAULT 0,
                    approved INTEGER DEFAULT 0
                    )
            ''')
    c.execute('''
              CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT, 
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              is_admin INTEGER DEFAULT 0
              )
            ''') 
            # Index 0 : user_id
            # Index 1 : username
            # Index 2 : password
            # Index 3: is_admin check
    conn.commit()
    conn.close()

@app.route('/create_account', methods=['GET', 'POST'])
def register():
    username = None
    password = None
    if request.method == 'POST':
        if username and password:
            return "Please fill out all fields."
        else:
            username = request.form['username']
            password = request.form['password']
            hashed_password = generate_password_hash(password)

            conn = sqlite3.connect('jokes.db')
            c = conn.cursor()

            try:
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()
            except sqlite3.IntegrityError:
                return "Username already taken."
            conn.close()

            return redirect('/')
    return render_template('create_account.html')


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        joke = request.form['joke']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('INSERT INTO jokes (content, timestamp) VALUES (?, ?)', (joke, timestamp))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('SELECT content, rating FROM jokes WHERE approved=1 ORDER BY rating DESC')
    jokes = c.fetchall()
    conn.close()
    return render_template('index.html', jokes=jokes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Getting user information when they type it in
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('SELECT id, password, is_admin FROM users WHERE username=?', (username,))
        user = c.fetchone() # fetch only one user
        conn.close()

        if user and check_password_hash(user[1], password): #check_password_hash checks the password with the hashed password (user[1]) to see if they match
            session['user_id'] = user[0] #set user_id
            session['username'] = username # set username 
            if user[2] == 1: #if user is_admin check
                session['admin'] = True
            else:
                session['admin'] = False
            return redirect('/') #go back to homepage 
        else:
            return 'Invalid credentials'
        
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/moderate')
def moderate():
    if not session.get('admin'):
        return redirect('/')
    
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('SELECT id, content, timestamp FROM jokes WHERE approved=0')
    jokes = c.fetchall()
    conn.close()
    return render_template('moderate.html', jokes=jokes)

@app.route('/approve/<int:joke_id>', methods=['POST'])
def approve_joke(joke_id):
    if not session.get('admin'):
        return '', 403
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('UPDATE jokes SET approved=1 WHERE id=?', (joke_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/reject/<int:joke_id>', methods=['POST'])
def reject_joke(joke_id):
    if not session.get('admin'):
        return '', 403
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('UPDATE jokes SET approved=1 WHERE id=?', (joke_id,))
    conn.commit()
    conn.close()
    return '', 204

if __name__ == "__main__":
    initdb()
    app.run(host="0.0.0.0", port=80)