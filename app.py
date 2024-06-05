from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import *
from flask_mail import Mail, Message
import mysql.connector
import bcrypt
from config import host, database, user, password

app = Flask(__name__)
app.config.from_pyfile('config.py')

mail = Mail(app)


conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
cur = conn.cursor() 
conn.commit() 
cur.close() 
conn.close() 

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/movie')
def movies():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor() 
    cur.execute('''SELECT * FROM film''') 
    data = cur.fetchall() 
    cur.close() 
    conn.close() 
  
    return render_template('filmy.html', data=data)
 
@app.route('/add_movie', methods=['POST'])
def add_movie():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor() 
  
    tytul = request.form['tytul'] 
    gatunek = request.form['gatunek'] 
    rezyser = request.form['rezyser']
    jezyk = request.form['jezyk'] 
    napisy = request.form['napisy']
    czas = request.form['czas']
    rok = request.form['rok']
  
    cur.execute( '''INSERT INTO film (tytul, gatunek, rezyser, jezyk, napisy, rok_wydania, czas_trwania) VALUES (%s, %s, %s, %s, %s, %s, %s)''', (tytul, gatunek, rezyser, jezyk, napisy, czas, rok)) 
    conn.commit() 
    cur.close() 
    conn.close() 
  
    return redirect(url_for('movies'))

@app.route('/delete_movie', methods=['POST']) 
def delete(): 
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor() 
    
    id = request.form['id_movie'] 
  
    cur.execute('''DELETE FROM film WHERE id_filmu=%s''', (id,)) 
  
    conn.commit() 
    cur.close() 
    conn.close() 
  
    return redirect(url_for('movies')) 
  
  
@app.route('/update_movie', methods=['POST']) 
def update(): 
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor() 
  
    tytul = request.form['tytul'] 
    gatunek = request.form['gatunek'] 
    rezyser = request.form['rezyser']
    jezyk = request.form['jezyk'] 
    napisy = request.form['napisy']
    czas = request.form['czas']
    rok = request.form['rok']
    id = request.form['id'] 
  
    cur.execute( '''UPDATE film SET tytul=%s, gatunek=%s, rezyser=%s, jezyk=%s, napisy=%s, rok_wydania=%s, czas_trwania=%s WHERE id_filmu=%s''', (tytul, gatunek, rezyser, jezyk, napisy, czas, rok, id)) 
  
    conn.commit() 
    return redirect(url_for('movies')) 
  
  
@app.route('/kina')
def cinemas():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM kino''')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('kina.html', data=data)

@app.route('/get_sala/<int:kino_id>')
def get_sala(kino_id):
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('''SELECT id_sali, nazwa, ilosc_miejsc FROM sala WHERE id_kina = %s''', (kino_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route('/get_availability/<int:sala_id>/<date>')
def get_availability(sala_id, date):
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('SELECT dostepna_godzina FROM dostepnosc_sali WHERE id_sali = %s AND dzien = %s', (sala_id, date))
    data = cur.fetchall()
    cur.close()
    conn.close()
    available_times = [str(time[0]) for time in data]
    return jsonify(available_times)


@app.route('/uzytkownicy')
def users():
    # Connect to the database 
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
  
    # create a cursor 
    cur = conn.cursor() 
  
    # Select all admins from the table 
    cur.execute('''SELECT id_uzytkownika, imie, nazwisko, mail FROM uzytkownik WHERE czy_admin = 1''') 
    admins = cur.fetchall()
  
    # Select all non-admin users from the table 
    cur.execute('''SELECT id_uzytkownika, imie, nazwisko, mail FROM uzytkownik WHERE czy_admin = 0''') 
    users = cur.fetchall()
  
    # close the cursor and connection 
    cur.close() 
    conn.close() 
  
    return render_template('uzytkownicy.html', admins=admins, users=users)

@app.route('/add_admin', methods=['POST'])
def add_admin():
    imie = request.form['imie']
    nazwisko = request.form['nazwisko']
    mail = request.form['mail']
    haslo = request.form['haslo']
    
    hashed_password = bcrypt.hashpw(haslo.encode('utf-8'), bcrypt.gensalt())
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('''INSERT INTO uzytkownik (imie, nazwisko, mail, haslo, czy_admin) VALUES (%s, %s, %s, %s, %s)''',
                (imie, nazwisko, mail, hashed_password, 1))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('users'))

@app.route('/remove_admin', methods=['POST'])
def remove_admin():
    id_klienta = request.form['id_klienta']
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('''UPDATE uzytkownik SET czy_admin = 0 WHERE id_uzytkownika = %s''', (id_klienta,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('users'))

@app.route('/register/', methods=['GET', 'POST'])
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

            flash('You have successfully registered', 'success')
            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            flash(f"An error occurred: {err}", 'error')
            conn.rollback()
        
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html', form=form)


@app.route('/login/', methods=['GET', 'POST'])
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
                if user_db['czy_admin'] == 1:  
                    session['admin'] = True
                else:
                    session['user'] = True
                return redirect(url_for('home')) 

            else:
                flash('Username or Password incorrect', "error")

        else:
            flash('User not found', "error")

        conn.close()

    return render_template('login.html', form=form)

@app.route('/logout/')
def logout():
    session.clear()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/contact', methods=['GET','POST'])
def contact():
    form = SendEmail(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        topic = form.topic.data
        text = form.text.data
        
        msg = Message(subject=topic,
                      sender='kino_111@outlook.com',
                      recipients=['kino_111@outlook.com'])
        msg.body = f"From: {name}\nEmail: {email}\nMessage: {text}"
        mail.send(msg)

        flash('Your message has been sent successfully!', 'success')
    return render_template('contact.html', form=SendEmail())


        
if __name__ == '__main__': 
    app.run(debug=True) 