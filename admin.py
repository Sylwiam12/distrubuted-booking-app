from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import mysql.connector
import bcrypt
from config import host, database, user, password
import datetime

admin_bp = Blueprint('admin', __name__, template_folder='templates')

@admin_bp.route('/movie')
def movies():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor() 
    cur.execute('''SELECT * FROM film''') 
    data = cur.fetchall() 
    cur.close() 
    conn.close() 
  
    return render_template('filmy.html', data=data)
 
@admin_bp.route('/add_movie', methods=['POST'])
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
  
    return redirect(url_for('admin.movies'))

@admin_bp.route('/delete_movie', methods=['POST']) 
def delete(): 
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor() 
    
    id = request.form['id_movie'] 
  
    cur.execute('''DELETE FROM film WHERE id_filmu=%s''', (id,)) 
  
    conn.commit() 
    cur.close() 
    conn.close() 
  
    return redirect(url_for('admin.movies')) 
  
  
@admin_bp.route('/update_movie', methods=['POST']) 
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
    return redirect(url_for('admin.movies')) 
  
  
@admin_bp.route('/kina')
def cinemas():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM kino''')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('kina.html', data=data)

@admin_bp.route('/get_sala/<int:kino_id>')
def get_sala(kino_id):
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('''SELECT id_sali, nazwa, ilosc_miejsc FROM sala WHERE id_kina = %s''', (kino_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@admin_bp.route('/get_availability/<int:sala_id>/<date>')
def get_availability(sala_id, date):
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('SELECT dostepna_godzina FROM dostepnosc_sali WHERE id_sali = %s AND dzien = %s', (sala_id, date))
    data = cur.fetchall()
    cur.close()
    conn.close()
    available_times = [str(time[0]) for time in data]
    return jsonify(available_times)

@admin_bp.route('/get_cinemas')
def get_cinemas():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute('SELECT id_kina, nazwa FROM kino')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@admin_bp.route('/add_availability', methods=['POST'])
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
            cur.execute('''
                SELECT COUNT(*)
                FROM zajete_godziny zg
                JOIN seans s ON zg.id_seansu = s.id_seansu
                WHERE zg.godzina = %s AND s.id_sali = %s AND s.data_seansu = %s
            ''', (time, sala_id, date))
            occupied_count = cur.fetchone()[0]
            
            if occupied_count == 0:
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


@admin_bp.route('/uzytkownicy')
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

@admin_bp.route('/add_admin', methods=['POST'])
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
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/remove_admin', methods=['POST'])
def remove_admin():
    id_klienta = request.form['id_klienta']
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('''UPDATE uzytkownik SET czy_admin = 0 WHERE id_uzytkownika = %s''', (id_klienta,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/seanse')
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

@admin_bp.route('/available_movies')
def available_movies():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('SELECT id_filmu, tytul, czas_trwania FROM film')
    movies = [{'id': row[0], 'title': row[1], 'duration': row[2]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(movies)

@admin_bp.route('/available_cinemas')
def available_cinemas():
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('SELECT id_kina, nazwa FROM kino')
    cinemas = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(cinemas)

@admin_bp.route('/available_halls')
def available_halls():
    kino_id = request.args.get('kino_id')
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('SELECT id_sali, nazwa FROM sala WHERE id_kina = %s', (kino_id,))
    halls = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(halls)

@admin_bp.route('/available_times')
def available_times():
    sala_id = request.args.get('sala_id')
    date = request.args.get('date')
    film_id = request.args.get('film_id')
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
    cur.execute('SELECT czas_trwania FROM film WHERE id_filmu = %s', (film_id,))
    duration = cur.fetchone()[0]
    
    cur.execute('''
        SELECT TIME_FORMAT(dostepna_godzina, '%H:%i')
        FROM dostepnosc_sali
        WHERE id_sali = %s AND dzien = %s
        ORDER BY dostepna_godzina
        ''', (sala_id, date))
    available_times = [row[0] for row in cur.fetchall()]

    available_start_times = []
    interval = 15  # minutes
    duration_in_minutes = duration  

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

from flask import request, render_template, redirect, url_for
import mysql.connector
from mysql.connector import Error

@admin_bp.route('/dodaj_seans', methods=['POST'])
def dodaj_seans():
    film_id = request.form['film']
    sala_id = request.form['sala']
    date = request.form['data']
    time = request.form['godzina']
    
    try:
        conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
        conn.start_transaction()
        cur = conn.cursor()

        # Get the movie duration
        cur.execute('SELECT czas_trwania FROM film WHERE id_filmu = %s', (film_id,))
        duration = cur.fetchone()[0]
        duration_in_minutes = duration  # assuming czas_trwania is in minutes

        # Calculate time slots to be used
        start_hour, start_minute = map(int, time.split(':'))
        interval = 15  # minutes

        times_to_check = [
            f"{(start_hour + (start_minute + i) // 60):02}:{(start_minute + i) % 60:02}"
            for i in range(0, duration_in_minutes, interval)
        ]

        # Check if all the times are available in the dostepnosc_sali table
        unavailable_times = []
        for check_time in times_to_check:
            cur.execute('SELECT 1 FROM dostepnosc_sali WHERE id_sali = %s AND dzien = %s AND dostepna_godzina = %s FOR UPDATE', 
                        (sala_id, date, check_time))
            if not cur.fetchone():
                unavailable_times.append(check_time)

        if unavailable_times:
            conn.rollback()
            return render_template('error.html', message=f"Time slots {', '.join(unavailable_times)} are not available for this seans.")

        # Proceed with inserting the seans
        cur.execute('''
            INSERT INTO seans (id_filmu, id_sali, data_seansu, godzina)
            VALUES (%s, %s, %s, %s)
            ''', (film_id, sala_id, date, time))
        
        seans_id = cur.lastrowid

        for del_time in times_to_check:
            cur.execute('DELETE FROM dostepnosc_sali WHERE id_sali = %s AND dzien = %s AND dostepna_godzina = %s', 
                        (sala_id, date, del_time))
            cur.execute('INSERT INTO zajete_godziny (godzina, id_seansu) VALUES (%s, %s)', 
                        (del_time, seans_id))
        
        conn.commit()
    except Error as e:
        conn.rollback()
        return render_template('error.html', message=f"An error occurred: {str(e)}")
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.seanse'))



@admin_bp.route('/delete_seans', methods=['POST'])
def delete_seans():
    id_seansu = request.form['id_seansu']
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    
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

    return redirect(url_for('admin.seanse'))