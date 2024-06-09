from flask import Flask, render_template, request, redirect, url_for, flash, session
from forms import *
from flask_mail import Mail, Message
import mysql.connector
from config import host, database, user, password
from admin import admin_bp
from auth import auth_bp
from user import user_bp

app = Flask(__name__)
app.config.from_pyfile('config.py')

mail = Mail(app)

app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)

conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
cur = conn.cursor() 
conn.commit() 
cur.close() 
conn.close() 

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__': 
    app.run(debug=True) 