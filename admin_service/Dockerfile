FROM python:3.9-slim

WORKDIR /distrubuted-booking-app/admin_service

COPY . /distrubuted-booking-app/admin_service

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENV FLASK_APP=admin.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
