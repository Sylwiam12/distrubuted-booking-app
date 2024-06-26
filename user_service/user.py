from flask import Flask, render_template, request, redirect, url_for, flash
from forms import *
from flask_mail import Mail, Message
import mysql.connector
from config import host, database, user, password, JWT_SECRET_KEY, JWT_ALGORITHM
import qrcode
import base64
from io import BytesIO
import jwt
from token_utils import *

user_app = Flask(__name__)
user_app.config.from_pyfile('config.py')
mail = Mail(user_app)


@user_app.route('/user/user_information')
def user_information():
    token = request.cookies.get('token')
    
    if not token:
        return redirect("/home/login")
    
    user_id = verify_token(token)[0]
    
    if not user_id:
        return redirect("/home/login")
    
    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor(dictionary=True)

    cur.execute('SELECT * FROM uzytkownik WHERE id_uzytkownika = %s', (user_id,))
    user_db = cur.fetchone()

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



@user_app.route('/user/catalog/')
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

@user_app.route('/user/book/')
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

@user_app.route('/user/book/cinema', methods=['POST'])
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

@user_app.route('/user/book/date', methods=['POST'])
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

@user_app.route('/user/book/time', methods=['POST'])
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

@user_app.route('/user/book/sala', methods=['POST'])
def pick_sala():
    id_filmu = request.form['id_filmu']
    id_kina = request.form['id_kina']
    date = request.form['date']
    time = request.form['time']

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    query = '''
        SELECT s.nazwa
        FROM sala s
        JOIN kino k ON s.id_kina = k.id_kina
        JOIN seans se ON s.id_sali = se.id_sali
        WHERE s.id_kina = %s AND se.data_seansu = %s AND se.godzina = %s;
    '''

    cur.execute(query, (id_kina, date, time ))

    rows = cur.fetchall()
    available_salas = [row[0] for row in rows]

    cur.close()
    conn.close()

    return render_template('book_sala.html', id_filmu=id_filmu, id_kina=id_kina, date=date, time=time, available_salas=available_salas)

@user_app.route('/user/book/seats', methods=['POST'])
def pick_seat():
    id_filmu = request.form['id_filmu']
    id_kina = request.form['id_kina']
    date = request.form['date']
    time = request.form['time']
    sala = request.form['sala']


    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()
    query = """ SELECT id_sali FROM sala WHERE id_kina = %s AND nazwa = %s; """
    cur.execute(query, (id_kina, sala))
    sala_id = cur.fetchone()[0]

    query = """
        SELECT z.rzad, z.numer
        FROM zajete_miejsce z
        JOIN rezerwacja r ON z.id_rezerwacji = r.id_rezerwacji
        JOIN seans s ON r.id_seansu = s.id_seansu
        WHERE s.id_filmu = %s AND s.data_seansu = %s AND s.godzina = %s AND s.id_sali = %s;
    """
    cur.execute(query, (id_filmu, date, time, sala_id))
    rows = cur.fetchall()
    reserved_seats = [(row[0], row[1]) for row in rows]


    sala_query = """
        SELECT ilosc_miejsc
        FROM sala 
        WHERE id_sali = %s ;
    """
    cur.execute(sala_query, (sala_id,))
    ilosc_miejsc = cur.fetchone()[0]
    rows_count = (ilosc_miejsc + 9) // 10

    all_seats = {row: list(range(1, 11)) for row in range(1, rows_count + 1)}

    for rzad, numer in reserved_seats:
        if rzad in all_seats and numer in all_seats[rzad]:
            all_seats[rzad].remove(numer)
        else:
            print(f"Warning: Seat {numer} in row {rzad} is reserved but not in the expected range.")

    cur.close()
    conn.close()

    return render_template('book_seats.html', id_filmu=id_filmu, id_kina=id_kina, date=date, time=time, all_seats=all_seats, sala_id=sala_id)

@user_app.route('/user/summary', methods=['GET', 'POST'])
def summary():
    token = request.cookies.get('token')


    if not token:
        return redirect("/home/login")
    
    user_id = verify_token(token)[0]
    
    if not user_id:
        return redirect("/home/login")

    if request.method == 'POST':
        id_filmu = request.form['id_filmu']
        id_kina = request.form['id_kina']
        date = request.form['date']
        time = request.form['time']
        sala_id = request.form['sala_id']
        rows = request.form.getlist('rows[]')
        seats = request.form.getlist('seats[]')
        ticket_types = request.form.getlist('ticket_types[]')
        

        conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
        cur = conn.cursor()

        cur.execute("SELECT nazwa FROM kino WHERE id_kina = %s", (id_kina,))
        cinema_name = cur.fetchone()[0]

        cur.execute("SELECT tytul FROM film WHERE id_filmu = %s", (id_filmu,))
        film_name = cur.fetchone()[0]

        cur.execute("""
            SELECT id_seansu FROM seans 
            WHERE id_filmu = %s AND data_seansu = %s AND godzina = %s AND id_sali = %s
        """, (id_filmu, date, time, sala_id))
        id_seansu = cur.fetchone()
        if id_seansu is None:
            cur.close()
            conn.close()
            return "Nie znaleziono seansu", 404
        id_seansu = id_seansu[0]

        cur.close()
        conn.close()

        seat_details = list(zip(rows, seats, ticket_types))
        total_cost = sum(18 if ticket == 'ulgowy' else 24 for ticket in ticket_types)

        return render_template('summary.html', id_filmu=id_filmu, id_kina=id_kina, date=date, time=time, seat_details=seat_details, total_cost=total_cost, film_name=film_name, cinema_name=cinema_name, id_seansu=id_seansu)
    
    return redirect("/home")


@user_app.route('/user/payment', methods=['POST'])
def payment():
    token = request.cookies.get('token')
    
    if not token:
        return redirect("/home/login")
    
    user_id = verify_token(token)[0]
    
    if not user_id:
        return redirect("/home/login")

    id_seansu = request.form['id_seansu']
    rows = request.form.getlist('rows[]')
    seats = request.form.getlist('seats[]')
    ticket_types = request.form.getlist('ticket_types[]')

    seat_details = list(zip(rows, seats, ticket_types))
    total_cost = sum(18 if ticket == 'ulgowy' else 24 for ticket in ticket_types)

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    conn.start_transaction()

    try:
        for row, seat in zip(rows, seats):
            cur.execute(
                "SELECT 1 FROM zajete_miejsce zm "
                "JOIN rezerwacja r ON zm.id_rezerwacji = r.id_rezerwacji "
                "WHERE r.id_seansu = %s AND zm.rzad = %s AND zm.numer = %s",
                (id_seansu, row, seat)
            )
            if cur.fetchone():
                conn.rollback()
                return render_template('error.html', message=f"Seat {row}-{seat} is already taken for this seans.")

        cur.execute(
            "INSERT INTO rezerwacja (id_uzytkownika, id_seansu, ilosc_miejsc) VALUES (%s, %s, %s)",
            (user_id, id_seansu, len(seat_details))
        )
        reservation_id = cur.lastrowid

        for row, seat, _ in seat_details:
            cur.execute(
                "INSERT INTO zajete_miejsce (id_rezerwacji, rzad, numer) VALUES (%s, %s, %s)",
                (reservation_id, row, seat)
            )

        conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        return render_template('error.html', message=f"Database error: {err}")
    finally:
        cur.close()
        conn.close()
        
        
    return render_template('payment.html', reservation_id=reservation_id, seat_details=seat_details, total_cost=total_cost)


@user_app.route('/user/payment/confirmation', methods=['POST'])
def payment_confirmation():
    token = request.cookies.get('token')
    
    if not token:
        return redirect("/user/login")
    
    user_id = verify_token(token)[0]
    
    if not user_id:
        return redirect("/user/login")
    
    reservation_id = request.form['reservation_id']
    confirmation = request.form['confirmation']

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    if confirmation == 'yes':
        try:
            cur.execute("INSERT INTO platnosc (id_rezerwacji, kwota, czas_rozpoczecia) VALUES (%s, %s, NOW())",
                        (reservation_id, request.form['total_cost']))
            conn.commit()
            return redirect(url_for('success', reservation_id=reservation_id))
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


@user_app.route('/user/payment/success')
def success():
    token = request.cookies.get('token')
    
    if not token:
        return redirect("/home/login")
    
    user_id = verify_token(token)[0]

    if not user_id:
        return redirect("/home/login")
    
    reservation_id = request.args.get('reservation_id')
    total_cost = request.args.get('total_cost')

    if not reservation_id:
        return "Nie znaleziono rezerwacji", 404

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute('''
            SELECT r.id_rezerwacji, r.ilosc_miejsc, s.id_sali, s.id_filmu, f.tytul AS film_title, s.data_seansu, s.godzina, k.nazwa AS cinema_name, z.rzad, z.numer
            FROM rezerwacja r
            JOIN seans s ON r.id_seansu = s.id_seansu
            JOIN film f ON s.id_filmu = f.id_filmu
            JOIN sala sa ON s.id_sali = sa.id_sali
            JOIN kino k ON sa.id_kina = k.id_kina
            JOIN zajete_miejsce z ON r.id_rezerwacji = z.id_rezerwacji
            WHERE r.id_rezerwacji = %s
        ''', (reservation_id,))
        reservations = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    if not reservations:
        return "Nie znaleziono rezerwacji", 404

    reservation = reservations[0]
    seat_details = [(res['rzad'], res['numer']) for res in reservations]

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=2,
    )
    qr.add_data(f'Reservation ID: {reservation_id}')
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')

    img_buffer = BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_data_url = f"data:image/png;base64,{base64.b64encode(img_buffer.read()).decode()}"

    return render_template('success.html', reservation=reservation, seat_details=seat_details, qr_data_url=qr_data_url, total_cost=total_cost)



@user_app.route('/user/payment/failure')
def failure():
    return render_template('failure.html')

@user_app.route('/user/contact', methods=['GET', 'POST'])
def contact():
    form = SendEmail(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        topic = form.topic.data
        text = form.text.data

        msg = Message(
            subject=topic,
            sender=user_app.config['MAIL_USERNAME'],
            recipients=[user_app.config['MAIL_USERNAME']]
        )
        msg.body = f"From: {name}\nEmail: {email}\nMessage: {text}"

        try:
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash('Failed to send your message. Please try again later.', 'error')

    return render_template('contact.html', form=form)


if __name__ == '__main__': 
    user_app.run(debug=True) 