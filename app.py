from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import *
from flask_mail import Mail, Message
import mysql.connector
import bcrypt
from config import host, database, user, password
import datetime

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

@app.route('/get_cinemas')
def get_cinemas():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('SELECT id_kina, nazwa FROM kino')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route('/add_availability', methods=['POST'])
def add_availability():
    req_data = request.get_json()
    sala_id = req_data['salaId']
    date = req_data['date']
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    times = [
        '10:00', '10:15', '10:30', '10:45', '11:00', '11:15', '11:30', '11:45',
        '12:00', '12:15', '12:30', '12:45', '13:00', '13:15', '13:30', '13:45',
        '14:00', '14:15', '14:30', '14:45', '15:00', '15:15', '15:30', '15:45',
        '16:00', '16:15', '16:30', '16:45', '17:00', '17:15', '17:30', '17:45',
        '18:00', '18:15', '18:30', '18:45', '19:00', '19:15', '19:30', '19:45',
        '20:00', '20:15', '20:30', '20:45', '21:00'
    ]
    
    success = True
    messages = 0
    try:
        for time in times:
            # Check if the time is already in zajete_godziny
            cur.execute('''
                SELECT COUNT(*)
                FROM zajete_godziny zg
                JOIN seans s ON zg.id_seansu = s.id_seansu
                WHERE zg.godzina = %s AND s.id_sali = %s AND s.data_seansu = %s
            ''', (time, sala_id, date))
            occupied_count = cur.fetchone()[0]
            
            if occupied_count == 0:
                # Check if the time is already in dostepnosc_sali
                cur.execute('''
                    SELECT COUNT(*)
                    FROM dostepnosc_sali
                    WHERE dzien = %s AND dostepna_godzina = %s AND id_sali = %s
                ''', (date, time, sala_id))
                available_count = cur.fetchone()[0]
                
                if available_count == 0:
                    cur.execute('''
                        INSERT INTO dostepnosc_sali (dzien, dostepna_godzina, id_sali)
                        VALUES (%s, %s, %s)
                    ''', (date, time, sala_id))
                    messages += 1
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        success = False
        messages = f'Error occurred: {str(e)}'
    finally:
        cur.close()
        conn.close()
    
    return jsonify({'success': success, 'messages': messages})


@app.route('/uzytkownicy')
def users():

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password) 
    cur = conn.cursor()  
    cur.execute('''SELECT id_uzytkownika, imie, nazwisko, mail FROM uzytkownik WHERE czy_admin = 1''') 
    admins = cur.fetchall()
    cur.execute('''SELECT id_uzytkownika, imie, nazwisko, mail FROM uzytkownik WHERE czy_admin = 0''') 
    users = cur.fetchall()
  
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

@app.route('/seanse')
def seanse():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT seans.id_seansu, sala.nazwa, kino.nazwa, film.tytul, seans.data_seansu, seans.godzina
        FROM seans
        JOIN sala ON seans.id_sali = sala.id_sali
        JOIN kino ON sala.id_kina = kino.id_kina
        JOIN film ON seans.id_filmu = film.id_filmu
        ''') 
    
    data = cur.fetchall() 
    
    cur.close()
    conn.close()
    
    return render_template('seansy.html', data=data)

@app.route('/available_movies')
def available_movies():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('SELECT id_filmu, tytul, czas_trwania FROM film')
    movies = [{'id': row[0], 'title': row[1], 'duration': row[2]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(movies)

@app.route('/available_cinemas')
def available_cinemas():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('SELECT id_kina, nazwa FROM kino')
    cinemas = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(cinemas)

@app.route('/available_halls')
def available_halls():
    kino_id = request.args.get('kino_id')
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('SELECT id_sali, nazwa FROM sala WHERE id_kina = %s', (kino_id,))
    halls = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(halls)

@app.route('/available_times')
def available_times():
    sala_id = request.args.get('sala_id')
    date = request.args.get('date')
    film_id = request.args.get('film_id')
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    # Get the movie duration
    cur.execute('SELECT czas_trwania FROM film WHERE id_filmu = %s', (film_id,))
    duration = cur.fetchone()[0]
    
    # Fetch available times as formatted strings
    cur.execute('''
        SELECT TIME_FORMAT(dostepna_godzina, '%H:%i')
        FROM dostepnosc_sali
        WHERE id_sali = %s AND dzien = %s
        ORDER BY dostepna_godzina
        ''', (sala_id, date))
    available_times = [row[0] for row in cur.fetchall()]

    available_start_times = []
    interval = 15  # minutes
    duration_in_minutes = duration  # assuming czas_trwania is in minutes

    for start_time in available_times:
        start_hour, start_minute = map(int, start_time.split(':'))
        start_datetime = datetime.datetime.strptime(start_time, '%H:%M')
        end_datetime = start_datetime + datetime.timedelta(minutes=duration_in_minutes)
        end_time_str = end_datetime.strftime('%H:%M')
        
        if all(
            (start_datetime + datetime.timedelta(minutes=i)).strftime('%H:%M') in available_times
            for i in range(0, duration_in_minutes, interval)
        ):
            available_start_times.append(start_time)

    cur.close()
    conn.close()
    
    return jsonify(available_start_times)

@app.route('/dodaj_seans', methods=['POST'])
def dodaj_seans():
    film_id = request.form['film']
    sala_id = request.form['sala']
    date = request.form['data']
    time = request.form['godzina']
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO seans (id_filmu, id_sali, data_seansu, godzina)
        VALUES (%s, %s, %s, %s)
        ''', (film_id, sala_id, date, time))
    
    seans_id = cur.lastrowid
    
    # Get the movie duration
    cur.execute('SELECT czas_trwania FROM film WHERE id_filmu = %s', (film_id,))
    duration = cur.fetchone()[0]
    duration_in_minutes = duration  # assuming czas_trwania is in minutes

    # Calculate time slots to be deleted
    start_hour, start_minute = map(int, time.split(':'))
    interval = 15  # minutes

    times_to_delete = [
        f"{(start_hour + (start_minute + i) // 60):02}:{(start_minute + i) % 60:02}"
        for i in range(0, duration_in_minutes, interval)
    ]
    
    for del_time in times_to_delete:
        cur.execute('DELETE FROM dostepnosc_sali WHERE id_sali = %s AND dzien = %s AND dostepna_godzina = %s', (sala_id, date, del_time))
        cur.execute('INSERT INTO zajete_godziny (godzina, id_seansu) VALUES (%s, %s)', (del_time, seans_id))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('seanse'))

@app.route('/delete_seans', methods=['POST'])
def delete_seans():
    id_seansu = request.form['id_seansu']
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    # Retrieve information about the seans to be deleted
    cur.execute('''
        SELECT id_filmu, id_sali, data_seansu, godzina
        FROM seans
        WHERE id_seansu = %s
    ''', (id_seansu,))
    seans_info = cur.fetchone()
    if seans_info:
        film_id, sala_id, date, time = seans_info

        # Convert time to string if it is a datetime object
        if isinstance(time, datetime.timedelta):
            total_seconds = int(time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time = f"{hours:02}:{minutes:02}"
        elif isinstance(time, datetime.time):
            time = time.strftime("%H:%M")

        # Delete the seans
        cur.execute('DELETE FROM seans WHERE id_seansu = %s', (id_seansu,))
        
        # Get the movie duration
        cur.execute('SELECT czas_trwania FROM film WHERE id_filmu = %s', (film_id,))
        duration = cur.fetchone()[0]
        duration_in_minutes = duration  # assuming czas_trwania is in minutes

        # Calculate time slots to be re-added to dostepnosc_sali
        start_hour, start_minute = map(int, time.split(':'))
        interval = 15  # minutes

        times_to_add = [
            f"{(start_hour + (start_minute + i) // 60):02}:{(start_minute + i) % 60:02}"
            for i in range(0, duration_in_minutes, interval)
        ]

        for add_time in times_to_add:
            cur.execute('''
                INSERT INTO dostepnosc_sali (id_sali, dzien, dostepna_godzina)
                VALUES (%s, %s, %s)
            ''', (sala_id, date, add_time))
            cur.execute('DELETE FROM zajete_godziny WHERE id_seansu = %s AND godzina = %s', (id_seansu, add_time))
        
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('seanse'))



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
                session['user_id'] = user_db['id_uzytkownika']
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

@app.route('/user_information')
def user_information():
    user_id = session['user_id']

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM uzytkownik WHERE id_uzytkownika = %s', (user_id,))
    user_db = cur.fetchone()

    cur.execute('''
        SELECT r.id_rezerwacji, r.id_seansu, r.ilosc_miejsc, 
               s.id_sali, s.id_filmu, s.data_seansu, s.godzina
        FROM rezerwacja r
        JOIN seans s ON r.id_seansu = s.id_seansu
        WHERE r.id_uzytkownika = %s
    ''', (user_id,))
    reservations = cur.fetchall()

    cur.close()
    conn.close()

    if user_db:
        return render_template('user_information.html', user=user_db, reservations=reservations)
    else:
        return "User not found", 404

@app.route('/catalog/')
def catalog():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('''SELECT id_filmu, tytul, rezyser, gatunek, jezyk, napisy, rok_wydania, czas_trwania FROM film''')
    data = cur.fetchall()
    cur.close()
    conn.close()

    films = []
    for row in data:
        film = {
            'id_filmu': row[0],
            'tytul': row[1],
            'rezyser': row[2],
            'gatunek': row[3],
            'jezyk': row[4],
            'napisy': row[5],
            'rok_wydania': row[6],
            'czas_trwania': row[7]
        }
        films.append(film)
    
    return render_template('catalog.html', films=films)
        
if __name__ == '__main__': 
    app.run(debug=True) 