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

            flash('Zostałeś pomyślnie zarejestrowany!', 'success')
            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            flash(f"Wystąpił błąd: {err}", 'error')
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
                flash('Nazwa użytkownika lub hałso są niepoprawne!', "error")

        else:
            flash('Nie znaleziono użytkownika!', "error")

        conn.close()

    return render_template('login.html', form=form)

@app.route('/logout/')
def logout():
    session.clear()
    flash('Wylogowanie przebiegło pomyślnie!', 'success')
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
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor(dictionary=True)
    
    # Fetch user information
    cur.execute('SELECT * FROM uzytkownik WHERE id_uzytkownika = %s', (user_id,))
    user_db = cur.fetchone()

    # Fetch reservations with additional details
    cur.execute('''
        SELECT r.id_rezerwacji, r.ilosc_miejsc, s.id_sali, s.id_filmu, f.tytul AS film_title, s.data_seansu, s.godzina, k.nazwa AS cinema_name, z.rzad, z.numer
        FROM rezerwacja r
        JOIN seans s ON r.id_seansu = s.id_seansu
        JOIN film f ON s.id_filmu = f.id_filmu
        JOIN sala sa ON s.id_sali = sa.id_sali
        JOIN kino k ON sa.id_kina = k.id_kina
        JOIN zajete_miejsce z ON r.id_rezerwacji = z.id_rezerwacji
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

@app.route('/book/')
def book_filmy():
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
    
    return render_template('book_filmy.html', films=films)

@app.route('/book/cinema', methods=['POST'])
def pick_cinema():
    id_filmu = request.form['id_filmu']
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('''SELECT id_kina, nazwa, lokalizacja FROM kino''')
    data = cur.fetchall()
    cur.close()
    conn.close()

    kina = []
    for row in data:
        kino = {
            'id_kina': row[0],
            'nazwa': row[1],
            'lokalizacja': row[2],
        }
        kina.append(kino)
    
    return render_template('book_cinema.html', id_filmu=id_filmu, kina=kina)

@app.route('/book/date', methods=['POST'])
def pick_date():
    id_filmu = request.form['id_filmu']
    id_kina = request.form['id_kina']
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT data_seansu FROM seans WHERE id_filmu = %s AND id_sali IN (SELECT id_sali FROM sala WHERE id_kina = %s) ORDER BY data_seansu", (id_filmu, id_kina))
    rows = cur.fetchall()
    available_dates = [row[0] for row in rows]

    cur.close()
    conn.close()

    return render_template('book_date.html', id_filmu=id_filmu, id_kina=id_kina, available_dates=available_dates)

@app.route('/book/time', methods=['POST'])
def pick_time():
    id_filmu = request.form['id_filmu']
    id_kina = request.form['id_kina']
    date = request.form['date']

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    query = "SELECT DISTINCT godzina FROM seans WHERE id_filmu = %s AND id_sali IN (SELECT id_sali FROM sala WHERE id_kina = %s) AND data_seansu = %s ORDER BY godzina"
    cur.execute(query, (id_filmu, id_kina, date))
    rows = cur.fetchall()
    available_times = [row[0] for row in rows]

    cur.close()
    conn.close()

    return render_template('book_time.html', id_filmu=id_filmu, id_kina=id_kina, date=date, available_times=available_times)
@app.route('/book/seats', methods=['POST'])
def pick_seat():
    id_filmu = request.form['id_filmu']
    id_kina = request.form['id_kina']
    date = request.form['date']
    time = request.form['time']

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    query = """
        SELECT z.rzad, z.numer
        FROM zajete_miejsce z
        JOIN rezerwacja r ON z.id_rezerwacji = r.id_rezerwacji
        JOIN seans s ON r.id_seansu = s.id_seansu
        WHERE s.id_filmu = %s AND s.data_seansu = %s AND s.godzina = %s;
    """
    cur.execute(query, (id_filmu, date, time))
    rows = cur.fetchall()
    reserved_seats = [(row[0], row[1]) for row in rows]

    sala_query = """
        SELECT sa.ilosc_miejsc
        FROM sala sa
        JOIN seans s ON sa.id_sali = s.id_sali
        WHERE s.id_filmu = %s AND s.data_seansu = %s AND s.godzina = %s;
    """
    cur.execute(sala_query, (id_filmu, date, time))
    ilosc_miejsc = cur.fetchone()[0]
    rows_count = (ilosc_miejsc + 9) // 10

    all_seats = {row: list(range(1, 11)) for row in range(1, rows_count + 1)}
    for rzad, numer in reserved_seats:
        all_seats[rzad].remove(numer)

    cur.close()
    conn.close()

    return render_template('book_seats.html', id_filmu=id_filmu, id_kina=id_kina, date=date, time=time, all_seats=all_seats)

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        id_filmu = request.form['id_filmu']
        id_kina = request.form['id_kina']
        date = request.form['date']
        time = request.form['time']
        rows = request.form.getlist('rows[]')
        seats = request.form.getlist('seats[]')
        ticket_types = request.form.getlist('ticket_types[]')

        conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
        cur = conn.cursor()

        # Fetch film and cinema names from the database based on their IDs
        cur.execute("SELECT nazwa FROM kino WHERE id_kina = %s", (id_kina,))
        cinema_name = cur.fetchone()[0]

        cur.execute("SELECT tytul FROM film WHERE id_filmu = %s", (id_filmu,))
        film_name = cur.fetchone()[0]

        # Fetch the id_seansu
        cur.execute("""
            SELECT id_seansu FROM seans 
            WHERE id_filmu = %s AND data_seansu = %s AND godzina = %s
        """, (id_filmu, date, time))
        id_seansu = cur.fetchone()
        if id_seansu is None:
            cur.close()
            conn.close()
            return "Seans not found", 404
        id_seansu = id_seansu[0]

        cur.close()
        conn.close()

        seat_details = list(zip(rows, seats, ticket_types))
        total_cost = sum(18 if ticket == 'ulgowy' else 24 for ticket in ticket_types)

        return render_template('summary.html', id_filmu=id_filmu, id_kina=id_kina, date=date, time=time, seat_details=seat_details, total_cost=total_cost, film_name=film_name, cinema_name=cinema_name, id_seansu=id_seansu)
    return redirect(url_for('index'))


@app.route('/payment', methods=['POST'])
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    id_seansu = request.form['id_seansu']
    rows = request.form.getlist('rows[]')
    seats = request.form.getlist('seats[]')
    ticket_types = request.form.getlist('ticket_types[]')

    seat_details = list(zip(rows, seats, ticket_types))
    total_cost = sum(18 if ticket == 'ulgowy' else 24 for ticket in ticket_types)

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    try:
        # Start a transaction
        conn.start_transaction()

        # Lock the seats to prevent double booking
        for row, seat in seat_details:
            cur.execute("""
                SELECT 1 
                FROM zajete_miejsce z
                JOIN rezerwacja r ON z.id_rezerwacji = r.id_rezerwacji
                JOIN seans s ON r.id_seansu = s.id_seansu
                WHERE s.id_seansu = %s AND z.rzad = %s AND z.numer = %s
                FOR UPDATE
            """, (id_seansu, row, seat))

        # Insert the reservation
        cur.execute("INSERT INTO rezerwacja (id_uzytkownika, id_seansu, ilosc_miejsc) VALUES (%s, %s, %s)", 
                    (user_id, id_seansu, len(seat_details)))
        reservation_id = cur.lastrowid

        # Insert each seat
        for row, seat, ticket in seat_details:
            cur.execute("INSERT INTO zajete_miejsce (id_rezerwacji, rzad, numer) VALUES (%s, %s, %s)", 
                        (reservation_id, row, seat))

        # Commit the transaction
        conn.commit()
    except mysql.connector.Error as err:
        # Rollback in case of error
        conn.rollback()
        raise err
    finally:
        cur.close()
        conn.close()

    return render_template('payment.html', reservation_id=reservation_id, seat_details=seat_details, total_cost=total_cost)



@app.route('/payment/confirmation', methods=['POST'])
def payment_confirmation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    reservation_id = request.form['reservation_id']
    confirmation = request.form['confirmation']

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    if confirmation == 'yes':
        try:
            cur.execute("INSERT INTO platnosc (id_rezerwacji, kwota, czas_rozpoczecia) VALUES (%s, %s, NOW())",
                        (reservation_id, request.form['total_cost']))
            conn.commit()
            return redirect(url_for('success'))
        except mysql.connector.Error as err:
            conn.rollback()
            return redirect(url_for('failure'))
    else:
        try:
            cur.execute("DELETE FROM zajete_miejsce WHERE id_rezerwacji = %s", (reservation_id,))
            cur.execute("DELETE FROM rezerwacja WHERE id_rezerwacji = %s", (reservation_id,))
            conn.commit()
            return redirect(url_for('failure'))
        except mysql.connector.Error as err:
            conn.rollback()
            return redirect(url_for('failure'))
    
@app.route('/payment/success')
def success():
    return render_template('success.html')

@app.route('/payment/failure')
def failure():
    return render_template('failure.html')



if __name__ == '__main__': 
    app.run(debug=True) 