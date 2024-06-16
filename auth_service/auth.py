from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, make_response
import datetime
import mysql.connector
from functools import wraps
from mysql.connector import connect
from werkzeug.security import generate_password_hash, check_password_hash
from config import host, database, user, password, JWT_SECRET_KEY, JWT_ALGORITHM, SECRET_KEY
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from forms import *
import atexit
import jwt
from datetime import timedelta, datetime
import time
from token_utils import *

auth_app = Flask(__name__)
auth_app.config.from_pyfile('config.py')

auth_app.secret_key = SECRET_KEY  # Ensure SECRET_KEY is set
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
        trigger=IntervalTrigger(minutes=2),  # Run once every 2 minutes
        id='delete_outdated_seanse',
        name='Delete outdated seanse',
        replace_existing=True)
    atexit.register(lambda: scheduler.shutdown())

start_scheduler()

@auth_app.route('/')
def home():
    token = request.cookies.get('token')
    user_access = None
    admin = None

    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('user_id')
            is_admin = payload.get('is_admin')
            
            if is_admin:
                admin = True
            else:
                user_access = True

        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass

    return render_template('index.html', user=user_access, admin=admin)

@auth_app.route('/register/', methods=['GET', 'POST'])
def register():
    form = SignupForm(request.form)
    
    if request.method == 'POST' and form.validate():
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        password_register = form.password.data

        hashed_password = generate_password_hash(password_register, method='pbkdf2:sha256')
        conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT MAX(id_uzytkownika) FROM uzytkownik')
            last_user_id = cursor.fetchone()[0]

            if last_user_id is None:
                user_id = 0
            else:
                user_id = last_user_id + 1

            cursor.execute('''
                INSERT INTO uzytkownik (id_uzytkownika, imie, nazwisko, mail, haslo, czy_admin) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, name, surname, email, hashed_password, 0))
            
            conn.commit()

            flash('Zostałeś pomyślnie zarejestrowany!', 'success')
            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            flash(f"Wystąpił błąd: {err}", 'error')
            conn.rollback()
        
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html', form=form)


@auth_app.route('/login/', methods=['GET', 'POST'])
def login():
    form = SigninForm(request.form)

    if request.method == 'POST' and form.validate():
        email = form.email.data
        password_login = form.password.data
        
        conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM uzytkownik WHERE mail = %s', (email,))
        user_db = cursor.fetchone()

        if user_db:
            if check_password_hash(user_db['haslo'], password_login):
                token = generate_token(user_db['id_uzytkownika'], user_db['czy_admin'])
                response = make_response(redirect(url_for('home')))  # Redirect to home page
                response.set_cookie('token', token, httponly=True, secure=True)
                return response

            else:
                flash('Nazwa użytkownika lub hałso są niepoprawne!', "error")

        else:
            flash('Nie znaleziono użytkownika!', "error")

        conn.close()

    return render_template('login.html', form=form)

@auth_app.route('/logout/')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('token', '', expires=0)
    flash('Wylogowanie przebiegło pomyślnie!', 'success')
    return response

if __name__ == '__main__':
    auth_app.run(debug=True)
