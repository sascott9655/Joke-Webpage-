# Jokes Webpage Project by Sam Scott
# Created 4/14/25
#---------------------------------------------------------------------------------------------------------------------------------------------
#Consideration: 1. conn = sqlite3.connect('jokes.db') 2. c = conn.cursor() 3. conn.commit() 4.  conn.close() these line of code are often used 
#maybe considering writing a function for these database calls
#---------------------------------------------------------------------------------------------------------------------------------------------
from flask import Flask, request, render_template, redirect, url_for, flash, session
import sqlite3
import os 
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')


def initdb():
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")  # Enable foreign key enforcement
    # c.execute("DROP TABLE IF EXISTS ratings")
    #--------------jokes table----------------------------------------------------------
    c.execute('''
            CREATE TABLE IF NOT EXISTS jokes (  -- jokes table for users to insert jokes
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_id INTEGER, --replacing this use instead of username
                rating REAL DEFAULT 0, 
                approved INTEGER DEFAULT 0,
                notified INTEGER DEFAULT 0,
                rejection_reason TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE 
                --Setting up the table with ON DELETE CASCADE, then deleting the user will automatically delete all related data(which is what we want!) 
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
                timestamp TEXT NOT NULL,
                UNIQUE(user_id, joke_id) --prevent multiple ratings per user per joke
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- checks to see if user_id exists in the users table and connects them 
                FOREIGN KEY (joke_id) REFERENCES jokes(id) ON DELETE CASCADE-- checks to see if joke_id exists in the jokes table and connects them 
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
                c.execute('INSERT INTO "users" ("username", "password") VALUES (?, ?)', (username, hashed_password))
                conn.commit()
                flash('Account created succesfully!', 'success')
            except sqlite3.IntegrityError:
                flash("Username already taken.", 'error')
                return render_template('create_account.html') #if account creating fails render back to it to try again
            conn.close()
            return redirect(url_for('index')) #login if successful
    
    return render_template('create_account.html') #default to the create account page 
  
@app.route("/", methods=['GET', 'POST'])
def index():
    # Connect to the database
    conn = sqlite3.connect('jokes.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Displays notification to the user if their joke is approved or not
    user_id = session.get('user_id')
    c.execute('''
            SELECT "id", "content", "approved", "rejection_reason"
            FROM "jokes"
            WHERE "user_id" = ? AND approved != 0 and notified = 0
            ''', (user_id,))
    notifications = c.fetchall()

    joke_ids = [joke['id'] for joke in notifications]

    # Set notified = 1 for jokes the user hasn't seen yet
    if joke_ids:
        placeholders = ','.join('?' for _ in joke_ids)
        c.execute(f'''
                UPDATE "jokes" 
                SET "notified" = 1
                WHERE "id" IN ({placeholders})''', joke_ids)
            
    # Clean up rejected jokes that the user has already seen  
    c.execute(f'''
        DELETE FROM "jokes"
        WHERE "approved" = -1 AND "notified" = 1
        ''')

    conn.commit()

    # Render jokes on the webpage 
    c.execute('''
               SELECT "jokes"."content", "jokes"."rating", "users"."username","jokes"."user_id", "jokes"."id"
               FROM "jokes"
               LEFT JOIN "users" ON "jokes"."user_id" = "users"."id"
               WHERE "jokes"."approved" = 1
               ORDER BY "jokes"."rating" DESC
               LIMIT 10
            ''')
    jokes = c.fetchall()

    conn.close()
    # Sending the list of jokes and having joke_comments have each joke_id match up to its associated comment
    # Need username=session.get('username') to check if a user is logged in or out
    return render_template('index.html', jokes=jokes, username=session.get('username'), notifications=notifications)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Getting user information when they type it in
    if request.method == 'POST':
        username = request.form['username'] #check if value is in the username box
        password = request.form['password'] #check if value is in the password box

        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('SELECT "id", "password", "is_admin" FROM "users" WHERE "username" = ?', (username,)) #check if username exists in db
        user = c.fetchone() # fetch the username if that's the case
        conn.close()

        if user and check_password_hash(user[1], password): #check if the username and password match
            session['user_id'] = user[0] #set user_id
            session['username'] = username # set username
            session['admin'] = (user[2] == 1) #check if they are admin
            flash(f'Welcome, {username}', 'success')
            return redirect(url_for('index')) #redirect back to the home page when you login 
        else:
            flash('Invalid username and/or password', 'error') 
            return render_template("login.html") #go back to login page 

    return render_template("login.html") #go back to the login page as default

@app.route('/logout')
def logout():
    username = session.get('username', '') #empty string if username doesnt exist
    session.clear() # Clears all session data (logs out user/admin)
    flash(f"You have been logged out, {username}", 'sad')
    return redirect(url_for('index')) #Takes you to the homepage

@app.route('/submit_joke', methods=['GET', 'POST'])
def submit_joke():
    if 'username' not in session:
        return redirect(url_for('login')) #cant submit a joke unless you are logged in
    if request.method == 'POST':
        joke = request.form['joke']
        user_id = session['user_id']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute('INSERT into "jokes" ("content", "timestamp", "user_id", "approved") VALUES (?, ?, ?, 0)', (joke, timestamp, user_id))
        conn.commit()
        conn.close()
        flash("Waiting for admin approval. Your joke should appear on the homepage if the joke is approved.", 'success')
        return redirect(url_for('index')) #if you are able to make a joke successfully then go to the homepage and wait for the admin to approve of it
    
    return render_template("submit_joke.html", user_id=session['user_id'])

@app.route('/moderate')
def moderate():
    conn = sqlite3.connect('jokes.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
                SELECT "jokes"."id", "jokes"."content", "jokes"."timestamp", "users".username 
                FROM "jokes"
                JOIN "users" ON "jokes"."user_id" = "users"."id"
                WHERE "approved" = 0
     ''') 
    jokes = c.fetchall() #find all unapproved jokes to moderate
    conn.close()

    return render_template('moderate.html', jokes=jokes)

@app.route('/delete_account', methods=['GET','POST'])
def delete_account():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method =='POST':
        user_id = session['user_id']
        conn = sqlite3.connect('jokes.db')
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys=ON")

        # Delete user — related jokes and ratings will be auto-deleted if ON DELETE CASCADE is set
        c.execute('DELETE FROM "users" WHERE "id" = ?', (user_id,))

        conn.commit()
        conn.close()
        session.clear()
        flash('Your account has been deleted.', 'sad')
        return redirect(url_for('index'))

    return render_template('delete_account.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        conn = sqlite3.connect('jokes.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        username = request.form.get('username')

        c.execute('''
                SELECT "id" FROM users
                WHERE "username" = ?
                ''',(username,))
        row = c.fetchone()
        conn.close()

        if row:
            user_id = row['id']
            return redirect(url_for('user_detail', user_id=user_id))
        else:
            flash('User not found', 'sad')
            return redirect(url_for('search'))

    return render_template('search.html') 


#These routes are dynamic routes in Flask. They extract the integer value joke_id from the URL and pass into the variable joke_id. 
@app.route('/approve/<int:joke_id>', methods=['POST'])
def approve_joke(joke_id):
    if not session.get('admin'):
        return '', 403 #block non-admins
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('UPDATE "jokes" SET "approved" = 1 WHERE "id" = ?', (joke_id,)) #update the home page if the joke is approved
    conn.commit()
    conn.close()
    flash('Joke approved', 'success')
    return redirect(url_for('moderate'))

@app.route('/reject/<int:joke_id>', methods=['POST'])
def reject_joke(joke_id):
    if not session.get('admin'):
        return '', 403
    reason = request.form.get('reason')
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('''
            UPDATE "jokes"
            SET approved = -1, rejection_reason = ?
            WHERE "id" = ?
            ''', (reason, joke_id,)
            )
    conn.commit()
    conn.close()
    flash(f'Joke rejected. Reason: {reason}', 'error')
    return redirect(url_for('moderate'))

@app.route('/delete_joke/<int:joke_id>', methods=['POST']) #This route is different from the reject route. It allows admins to delete jokes from the homepage(probably a temporary feature)
def delete_joke(joke_id):
    if not session.get('admin'):
        flash("Unauthorized: Only admins can delete jokes.", 'error')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()
    c.execute('DELETE FROM "jokes" WHERE "id" = ?', (joke_id,)) 
    conn.commit()
    conn.close()
    flash("Joke deleted." 'success')
    return redirect(url_for('index'))

@app.route('/rate_joke/<int:joke_id>', methods=['POST']) 
def rate_joke(joke_id):
    if 'user_id' not in session: #checks if the user_id is in the session dictionary and user_id is a key, and keys in Python dictionary are strings.
        flash("You must be logged in to rate jokes.", 'error')
        return redirect(url_for('login'))
    
    rating = int(request.form['rating'])
    user_id = session['user_id']
    comment = request.form.get('comment', '').strip() #do I want comment to be able to be empty? Testing needed to confirm
    # Format: Abbreviated weekday, month, 2-digit year
    timestamp = datetime.now().strftime("%B %d, %Y")

    if not rating or not comment:
        flash("You must provide both a rating and a comment.", 'error')
        return redirect(url_for('index'))

    conn = sqlite3.connect('jokes.db')
    c = conn.cursor()

    c.execute('''INSERT OR REPLACE INTO "ratings" ("user_id", "joke_id", "rating", "comment", "timestamp") --The INSERT OR REPLACE statement in SQLITE is used to add a new row or replace an existing row.
    -- This is useful because if you are a user you can rewrite a new review and have your new review overwrite the old one
    VALUES (?,?,?,?,?)
    ON CONFLICT("user_id", "joke_id") --If there is already a record for this user and joke, a conflict will occur(b/c user_id and joke_id are primary keys)
    DO UPDATE SET "rating" = excluded."rating", "comment" = excluded."comment", "timestamp" = excluded."timestamp" -- Update the existing rating, timestamp and comment with new values instead of throwing an error.
    ''',
    (user_id, joke_id, rating, comment, timestamp)) 

    c.execute('''
              UPDATE "jokes" --modifying the jokes table
              SET "rating" = ( --subquery that updates the rating column in the jokes table, and the new value comes from the average of the ratings from the ratings table
                  SELECT ROUND(AVG("rating"), 1)
                  FROM "ratings"
                  WHERE "joke_id" = ?
              )
              WHERE "id" = ? --ensures you are updating only the joke you are rating and that it matches to the joke_id in the subquery
              ''', (joke_id, joke_id) # first joke_id is the subquery the second joke_id is the jokes table column jokes_id 
              ) 
    conn.commit()
    conn.close()

    flash("Your rating and comment have been submitted.", 'success')
    return redirect(url_for('index'))

# This route is just for the jokes that make it on the homepage 
@app.route('/joke_detail/<int:joke_id>')
def joke_detail(joke_id):
    conn = sqlite3.connect('jokes.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Joke info
    c.execute('''
            SELECT "jokes"."id", "jokes"."content", "jokes"."rating", "users"."username"
            FROM "jokes"
            JOIN "users" ON "jokes"."user_id" = "users"."id"
            WHERE "jokes"."id" = ?
            ''', (joke_id,))
    row = c.fetchone()
    
    if row is None:
        flash("Joke not found.", 'error')
        return redirect(url_for('index'))

    joke = {
        'id': row[0],
        'content': row[1],
        'rating': row[2],
        'username': row[3]
    }
    # Comments 
    c.execute('''
            SELECT "ratings"."comment", "users"."username", "ratings"."rating", "ratings"."timestamp"
            FROM "ratings"
            JOIN "users" ON "ratings"."user_id" = "users"."id"
            WHERE "ratings"."joke_id" = ?
            ORDER BY ratings.timestamp DESC
            ''', (joke_id,))

    comments = []
    for row in c.fetchall():
        comments.append({
            'comment':row[0],
            'username': row[1],
            'rating': row[2],
            'timestamp': row[3]
        })
    conn.close()

    return render_template('joke_detail.html', joke=joke, comments=comments)  

@app.route('/user_detail/<int:user_id>')
def user_detail(user_id):
    conn = sqlite3.connect('jokes.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Jokes
    c.execute('''
            SELECT "jokes"."id", "jokes"."content", "jokes"."rating", "users"."username"
            FROM "jokes"
            JOIN "users" ON "jokes"."user_id" = "users"."id"
            WHERE "users"."id" = ?
            ''', (user_id,))

    jokes = []
    joke_ids = []
    for row in c.fetchall():
        jokes.append({
            'id': row['id'],
            'content': row['content'],
            'rating': row['rating'],
            'username': row['username']
        })
        joke_ids.append(row['id'])

    if not jokes:
        flash("User has no jokes uploaded." , 'sad')
        return redirect(url_for('search'))

    # Fetch all comments *on this user's jokes*
    if joke_ids:
        placeholders = ','.join('?' for _ in joke_ids)
        c.execute(f'''
                SELECT "ratings"."comment", "users"."username", "ratings"."rating", "ratings"."timestamp", "ratings"."joke_id"
                FROM "ratings"
                JOIN "users" ON "ratings"."user_id" = "users"."id"
                WHERE "ratings"."joke_id" IN ({placeholders})
                ORDER BY "ratings"."timestamp" DESC
                ''', joke_ids)

        comments = defaultdict(list) #Made this a default dict so you are able to fetch comments based on the joke id and not all the comments associated with that user

        for row in c.fetchall():
            comments[row['joke_id']].append({
                'comment': row['comment'],
                'username': row['username'],
                'rating': row['rating'],
                'timestamp': row['timestamp']
            })

    conn.close()

    return render_template('user_detail.html', jokes=jokes, comments=comments)

        

if __name__ == "__main__":
    initdb()
    app.run(host="0.0.0.0", port=80)