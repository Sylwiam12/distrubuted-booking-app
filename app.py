from flask import Flask, render_template, request, redirect, url_for, flash, session
from forms import *
from flask_mail import Mail, Message
import mysql.connector
from config import host, database, user, password
from admin import admin_bp
from auth import auth_bp

app = Flask(__name__)
app.config.from_pyfile('config.py')

mail = Mail(app)

app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)

conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
cur = conn.cursor() 
conn.commit() 
cur.close() 
conn.close() 

@app.route('/')
def home():
    return render_template('index.html')


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

    # Ensure that all lists have the same length
    if len(rows) != len(seats) or len(seats) != len(ticket_types):
        return "Mismatched seat selection data", 400

    seat_details = list(zip(rows, seats, ticket_types))
    total_cost = sum(18 if ticket == 'ulgowy' else 24 for ticket in ticket_types)

    conn = mysql.connector.connect(host=host, database=database, user=user, password=password)
    cur = conn.cursor()

    try:
        # Start a transaction
        conn.start_transaction()

        # Lock the seats to prevent double booking
        for row, seat, _ in seat_details:
            cur.execute("""
                SELECT 1 
                FROM zajete_miejsce z
                JOIN rezerwacja r ON z.id_rezerwacji = r.id_rezerwacji
                JOIN seans s ON r.id_seansu = s.id_seansu
                WHERE s.id_seansu = %s AND z.rzad = %s AND z.numer = %s
                FOR UPDATE
            """, (id_seansu, row, seat))
            # Fetch the result to avoid the "Unread result found" error
            cur.fetchall()

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