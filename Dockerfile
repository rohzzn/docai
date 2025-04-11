# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /webapp

# Install system dependencies required for Python packages or your application
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY ./webapp /webapp

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Collect static files
# Note: Comment this out if you handle static files differently in production
RUN python3 manage.py collectstatic --noinput

WORKDIR /webapp

# Command to run the Django development server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]