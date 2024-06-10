from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import mysql.connector
from config import host, database, user, password
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

app = Flask(__name__)
app.config.from_pyfile('config.py')

conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
cur = conn.cursor() 
conn.commit() 
cur.close() 
conn.close() 

def delete_outdated_seanse():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    try:
        current_date = datetime.now().date()
        cur.execute('DELETE FROM seans WHERE data_seansu < %s', (current_date,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=delete_outdated_seanse,
        trigger=IntervalTrigger(hours=24),  # Run once every 24 hours
        id='delete_outdated_seanse',
        name='Delete outdated seanse',
        replace_existing=True)
    atexit.register(lambda: scheduler.shutdown())

start_scheduler()

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__': 
    app.run(debug=True, host="0.0.0.0", port=8000) 