#!/bin/bash

# Check if prod parameter is set to "true"
if [ "$1" = "true" ]; then
    echo "Running makemigrations..."
    python manage.py makemigrations

    echo "Running migrate..."
    python manage.py migrate

    echo "Starting Gunicorn server..."
    gunicorn -w 4 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker period_tracking_BE.asgi:application
else
    echo "Running makemigrations..."
    python manage.py makemigrations

    echo "Running migrate..."
    python manage.py migrate

    echo "Starting Django development server..."
    python manage.py runserver
fi
