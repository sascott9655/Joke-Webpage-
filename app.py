from flask import Flask, request, render_template, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

def initdb():
    conn = sqlite3.connect('jokes.db')
    conn.cursor().execute('''
                CREATE TABLE IF NOT EXISTS jokes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    rating REAL DEFAULT 0,
                    approved INTEGER DEFAULT 0
                    )
            ''')
    conn.commit()
    conn.close()

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

if __name__ == "__main__":
    initdb()
    app.run(host="0.0.0.0", port=80)