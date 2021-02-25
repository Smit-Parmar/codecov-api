#!/bin/sh

# starts the development server using gunicorn
# NEVER run production with the --reload option command
echo "Starting gunicorn in dev mode"
export PYTHONWARNINGS=always
gunicorn codecov.wsgi:application --reload --bind 0.0.0.0:8000 --access-logfile '-'
