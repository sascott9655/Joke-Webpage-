# Jokes Webpage Project by Sam Scott
# Created 4/14/25
#---------------------------------------------------------------------------------------------------------------------------------------------
#Consideration: 1. conn = sqlite3.connect('jokes.db') 2. c = conn.cursor() 3. conn.commit() 4.  conn.close() these line of code are often used 
#maybe considering writing a function for these database calls
#---------------------------------------------------------------------------------------------------------------------------------------------
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
    c.execute("PRAGMA foreign_keys = ON")  # Enable foreign key enforcement
    #--------------jokes table----------------------------------------------------------
    c.execute('''
            CREATE TABLE IF NOT EXISTS jokes (  -- jokes table for users to insert jokes
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                username TEXT,
                rating REAL DEFAULT 0, 
                approved INTEGER DEFAULT 0
            )
            ''')
    #--------------users table----------------------------------------------------------
    c.execute('''
              CREATE TABLE IF NOT EXISTS users ( --users table 
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
              )
              ''') 
    #--------------ratings table--------------------------------------------------------
    c.execute('''
              CREATE TABLE  IF NOT EXISTS ratings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                joke_id INTEGER,
                rating INTEGER,
                comment TEXT,
                UNIQUE(user_id, joke_id) --prevent multiple ratings per user per joke
                FOREIGN KEY (user_id) REFERENCES users(id) -- checks to see if user_id exists in the users table and connects them 
                FOREIGN KEY (joke_id) REFERENCES jokes(id) -- checks to see if joke_id exists in the jokes table and connects them 
              )
              ''')
    conn.commit()
    conn.close()

@app.route('/create_account', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
            password = request.form['password'] #Content in the password box
            username = request.form['username'] #Content in the username box
            
            hashed_password = generate_password_hash(password) #have password hashed for security purposes
            conn = sqlite3.connect('jokes.db')
            c = conn.cursor()
            
            #try catch block to check if username has not been used and for the username and password to match
            try:
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()
                flash('Account created succesfully!')
            except sqlite3.IntegrityError:
                flash("Username already taken.")
                return render_template('create_account.html') #if account creating fails render back to it to try again
            conn.close()
            return redirect(url_for('login')) #login if successful
    
    return render_template('create_account.html') #default to the create account page 


@app.route("/", methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect('jokes.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT content, rating, username, id FROM jokes WHERE approved=1 ORDER BY rating DESC')
    jokes = c.fetchall()
    c.execute('''
            SELECT ratings.joke_id, ratings.comment, ratings.rating, users.username
            FROM ratings
            JOIN users ON ratings.user_id = users.id
            '''
            )
    comments = c.fetchall()

    joke_comments = {}
    for row in comments:
        joke_id = row['joke_id']
        if joke_id not in joke_comments:
            joke_comments[joke_id] = []
        joke_comments[joke_id].append({
            'username': row['username'],
            'rating': row['rating'],
            'comment': row['comment']
        })


    conn.close()
    # Sending the list of jokes and having joke_comments have each joke_id match up to its associated comment
    # Need username=session.get('username') to check if a user is logged in or out
    return render_template('index.html', jokes=jokes, username=session.get('username'), joke_comments=joke_comments)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Getting user information when they type it in
    if request.method == 'POST':
        username = request.form['username'] #check if value is in the username box
        password = request.form['password'] #check if value is in the password box

        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('SELECT id, password, is_admin FROM users WHERE username=?', (username,)) #check if username exists in db
        user = c.fetchone() # fetch the username if that's the case
        conn.close()

        if user and check_password_hash(user[1], password): #check if the username and password match
            session['user_id'] = user[0] #set user_id
            session['username'] = username # set username
            session['admin'] = (user[2] == 1) #check if they are admin
            flash(f'Welcome back,{username}')
            return redirect(url_for('index')) #redirect back to the home page when you login 
        else:
            flash('Invalid username') 
            return render_template("login.html") #go back to login page 

    return render_template("login.html") #go back to the login page as default

@app.route('/logout')
def logout():
    username = session.get('username', '') #empty string if username doesnt exist
    session.clear() # Clears all session data (logs out user/admin)
    flash(f"You have been logged out, {username}")
    return redirect(url_for('index')) #Takes you to the homepage

@app.route('/submit_joke', methods=['GET', 'POST'])
def submit_joke():
    if 'username' not in session:
        return redirect(url_for('login')) #cant submit a joke unless you are logged in
    if request.method == 'POST':
        joke = request.form['joke']
        username = session['username']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('INSERT into jokes (content, timestamp, username) VALUES (?, ?, ?)', (joke, timestamp, username))
        conn.commit()
        conn.close()
        flash("Waiting for admin approval. Your joke should appear on the homepage if the joke is approved.")
        return redirect(url_for('index')) #if you are able to make a joke successfully then go to the homepage and wait for the admin to approve of it
    
    return render_template("submit_joke.html", username=session['username'])

@app.route('/moderate')
def moderate():
    if not session.get('admin'):
        flash("Access denied. Admin privileges required.") #Admin approval to moderate
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('SELECT id, content, timestamp FROM jokes WHERE approved=0') 
    jokes = c.fetchall() #find all unapproved jokes to moderate
    conn.close()

    return render_template('moderate.html', jokes=jokes)

#These routes are dynamic routes in Flask. They extract the integer value joke_id from the URL and pass into the variable joke_id. 

@app.route('/approve/<int:joke_id>', methods=['POST'])
def approve_joke(joke_id):
    if not session.get('admin'):
        return '', 403 #block non-admins
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('UPDATE jokes SET approved=1 WHERE id=?', (joke_id,)) #update the home page if the joke is approved
    conn.commit()
    conn.close()
    return '', 204 #no content, but request is successful 

@app.route('/reject/<int:joke_id>', methods=['POST'])
def reject_joke(joke_id):
    if not session.get('admin'):
        return '', 403
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('DELETE FROM jokes WHERE id=?', (joke_id,)) #delete the joke from the database
    conn.commit()
    conn.close()
    flash('Joke rejected')
    return '', 204

@app.route('/delete_joke/<int:joke_id>', methods=['POST']) #This route is different from the reject route. It allows admins to delete jokes from the homepage(probably a temporary feature)
def delete_joke(joke_id):
    if not session.get('admin'):
        flash("Unauthorized: Only admins can delete jokes.")
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('DELETE FROM jokes WHERE id=?', (joke_id,)) 
    conn.commit()
    conn.close()

    flash("Joke deleted.")
    return redirect(url_for('index'))

@app.route('/rate_joke/<int:joke_id>', methods=['POST']) 
def rate_joke(joke_id):
    if 'user_id' not in session: #checks if the user_id is in the session dictionary and user_id is a key, and keys in Python dictionary are strings.
        flash("You must be logged in to rate jokes.")
        return redirect(url_for('login'))
    
    rating = int(request.form['rating'])
    user_id = session['user_id']
    comment = request.form.get('comment', '').strip() #do I want comment to be able to be empty? Testing needed to confirm

    if not rating or not comment:
        flash("You must provide both a rating and a comment.")
        return redirect(url_for('index'))

    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()

    c.execute('''INSERT OR REPLACE INTO ratings(user_id, joke_id, rating, comment) --The INSERT OR REPLACE statement in SQLITE is used to add a new row or replace an existing row.
    -- This is useful because if you are a user you can rewrite a new review and have your new review overwrite the old one
    VALUES (?,?,?,?)
    ON CONFLICT(user_id, joke_id) --If there is already a record for this user and joke, a conflict will occur(b/c user_id and joke_id are primary keys)
    DO UPDATE SET rating = excluded.rating, comment=excluded.comment -- Update the existing rating adn comment with new values instead of throwing an error.
    ''',
    (user_id, joke_id, rating, comment)) 

    c.execute('''
              UPDATE jokes --modifying the jokes table
              SET rating = ( --subquery that updates the rating column in the jokes table, and the new value comes from the average of the ratings from the ratings table
                  SELECT ROUND(AVG(rating), 1)
                  FROM ratings
                  WHERE joke_id=?
              )
              WHERE id=? --ensures you are updating only the joke you are rating and that it matches to the joke_id in the subquery
              ''', (joke_id, joke_id) # first joke_id is the subquery the second joke_id is the jokes table column jokes_id 
              ) 
            #test before 
    # c.execute('''
    #         SELECT ratings.comment, ratings.rating, users.username
    #         FROM ratings
    #         JOIN users ON ratings.user_id = users.id
    #         WHERE ratings, joke_id=?
    #         '''(joke_id,)
    #         )
    conn.commit()
    conn.close()

    flash("Your rating and comment have been submitted.")
    return redirect(url_for('index'))

     

if __name__ == "__main__":
    initdb()
    app.run(host="0.0.0.0", port=80)