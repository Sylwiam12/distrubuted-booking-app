# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /distrubuted-booking-app-1/admin_service

# Copy the current directory contents into the container at /app
COPY . /distrubuted-booking-app-1/admin_service

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV FLASK_APP=admin.py

# Run admin.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
