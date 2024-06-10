from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
import datetime
import mysql.connector
from functools import wraps
from mysql.connector import connect
from werkzeug.security import generate_password_hash, check_password_hash
from config import host, database, user, password, SECRET_KEY
from forms import SigninForm, SignupForm

auth_app = Flask(__name__)
auth_app.secret_key = SECRET_KEY  # Ensure SECRET_KEY is set

@auth_app.route('/register/', methods=['GET', 'POST'])
def register():
    form = SignupForm(request.form)
    
    if request.method == 'POST' and form.validate():
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        password_register = form.password.data

        hashed_password = generate_password_hash(password_register, method='pbkdf2:sha256')
        conn = mysql.connector.connect(host=host, database=database, user= user, password = password)
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
        
        conn = mysql.connector.connect(host=host, database=database, user= user, password= password)
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM uzytkownik WHERE mail = %s', (email,))
        user_db = cursor.fetchone()

        if user_db:
            if check_password_hash(user_db['haslo'], password_login):
                session['logged'] = True
                session['user_id'] = user_db['id_uzytkownika']
                if user_db['czy_admin'] == 1:  
                    session['admin'] = True
                else:
                    session['user'] = True
                return redirect("http://localhost:8000") 

            else:
                flash('Nazwa użytkownika lub hałso są niepoprawne!', "error")

        else:
            flash('Nie znaleziono użytkownika!', "error")

        conn.close()

    return render_template('login.html', form=form)

@auth_app.route('/logout/')
def logout():
    session.clear()
    flash('Wylogowanie przebiegło pomyślnie!', 'success')
    return redirect(url_for('login'))  # Redirect to login instead of home

@auth_app.route('/home')
def home():
    return render_template('home.html')  # Add a home route for testing

if __name__ == '__main__':
    auth_app.run(debug=True,host="0.0.0.0", port=8001)
