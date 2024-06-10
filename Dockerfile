FROM python:3.9
WORKDIR /distrubuted-booking-app
COPY requirements.txt /distrubuted-booking-app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /distrubuted-booking-app
EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0"]