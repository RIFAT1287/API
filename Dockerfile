# Use the official Python image as base image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip
RUN pip install --no-cache-dir -U pip

# Install project dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -U -r requirements.txt

# Expose the port your app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
