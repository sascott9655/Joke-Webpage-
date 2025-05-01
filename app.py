from flask import Flask, request, render_template, redirect, url_for, flash, session
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
            username TEXT,
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
    if request.method == 'POST':
            password = request.form['password'] #Content in the password box
            username = request.form['username'] #Content in the username box
            
            hashed_password = generate_password_hash(password)
            conn = sqlite3.connect('jokes.db')
            c = conn.cursor()

            try:
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()
                flash('Account created succesfully!')
            except sqlite3.IntegrityError:
                flash("Username already taken.")
                return render_template('create_account.html')
            conn.close()
            return redirect(url_for('login'))
    
    return render_template('create_account.html')


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not session.get('username'):
            flash("You must be logged in to submit jokes.")
            return redirect(url_for('login'))
        
        joke = request.form['joke']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = session.get('username') # get username from session if logged in
        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('INSERT INTO jokes (content, timestamp, username) VALUES (?, ?, ?)', (joke, timestamp,username))
        conn.commit()
        conn.close()
        flash("Joke submitted for approval!")
        return redirect(url_for('index'))

    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('SELECT content, rating, username FROM jokes WHERE approved=1 ORDER BY rating DESC')
    jokes = c.fetchall()
    conn.close()

    return render_template('index.html', jokes=jokes, username=session.get('username'))


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
            session['admin'] = (user[2] == 1)
            
            flash(f'Welcome back,{username}')
            return redirect(url_for('index')) 
        else:
            flash('Invalid username')
            return render_template("login.html") #go back to login page

    return render_template("login.html")

@app.route('/logout')
def logout():
    username = session.get('username', '')
    session.clear() # Clears all session data (logs out user/admin)
    flash(f"You have been logged out, {username}")
    return redirect(url_for('index')) #Takes you to the homepage

@app.route('/submit_joke', methods=['GET', 'POST'])
def submit_joke():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        joke = request.form['joke']
        username = session['username']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('INSERT into jokes (content, timestamp, username) VALUES (?, ?, ?)', (joke, timestamp, username))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))
    
    return render_template("submit_joke.html", username=session['username'])

@app.route('/moderate')
def moderate():
    if not session.get('admin'):
        flash("Access denied. Admin privileges required.")
        return redirect(url_for('index'))
    
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
    c.execute('DELETE FROM jokes WHERE id=?', (joke_id,))
    conn.commit()
    conn.close()
    flash('Joke rejected')
    return '', 204

if __name__ == "__main__":
    initdb()
    app.run(host="0.0.0.0", port=80)