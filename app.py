from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey' # Change this in production
app.config['SESSION_TYPE'] = 'filesystem'

# Admin credentials
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
    conn.commit()
    conn.close()

@app.route('/create_account', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash("Please fill out all fields.")
            return render_template('create_account.html')
            
        hashed_password = generate_password_hash(password)
        
        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                     (username, hashed_password))
            conn.commit()
            flash("Account created successfully!")
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
        
        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('INSERT INTO jokes (content, timestamp) VALUES (?, ?)', 
                 (joke, timestamp))
        conn.commit()
        conn.close()
        
        flash("Joke submitted for approval!")
        return redirect(url_for('index'))

    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('SELECT content, rating FROM jokes WHERE approved=1 ORDER BY rating DESC')
    jokes = c.fetchall()
    conn.close()

    username = session.get('username')
    return render_template('index.html', jokes=jokes, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('SELECT id, password, is_admin FROM users WHERE username=?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['admin'] = (user[2] == 1)
            
            flash(f"Welcome back, {username}!")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route('/logout')
def logout():
    username = session.get('username', '')
    session.clear()
    flash(f"Goodbye, {username}! You have been logged out.")
    return redirect(url_for('index'))

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
    
    flash("Joke approved!")
    return redirect(url_for('moderate'))

@app.route('/reject/<int:joke_id>', methods=['POST'])
def reject_joke(joke_id):
    if not session.get('admin'):
        return '', 403
        
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('DELETE FROM jokes WHERE id=?', (joke_id,))
    conn.commit()
    conn.close()
    
    flash("Joke rejected!")
    return redirect(url_for('moderate'))

@app.route('/rate/<int:joke_id>', methods=['POST'])
def rate_joke(joke_id):
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Login required'}), 401
        
    rating = float(request.form.get('rating', 0))
    if rating < 0 or rating > 5:
        return jsonify({'success': False, 'message': 'Invalid rating'}), 400
        
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('UPDATE jokes SET rating=? WHERE id=?', (rating, joke_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/top_ten_jokes')
def top_ten_jokes():
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('SELECT content, rating FROM jokes WHERE approved=1 ORDER BY rating DESC LIMIT 10')
    jokes = c.fetchall()
    conn.close()
    
    return render_template('top_jokes.html', jokes=jokes)



@app.route('/api/logout', methods=['POST'])
def api_logout():
    return jsonify({'success': True})

if __name__ == "__main__":
    initdb()
    app.run(host="0.0.0.0", port=80, debug=True)