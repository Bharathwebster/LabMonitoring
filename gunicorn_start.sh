#!/bin/bash

# Name of the application
NAME="baymonitoring_site"

# Django project directory
DJANGODIR=/BayMointor/LabMonitor/src/


DJANGO_SETTINGS_MODULE=baymonitoring.settings

# WSGI module name
DJANGO_WSGI_MODULE=baymonitoring.wsgi

echo "STARTING mysite"

# Activate the virtual environment
cd $DJANGODIR
source ../../envs/bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

echo "gonna execute..."
exec ../../envs/bin/gunicorn $DJANGO_WSGI_MODULE:application --workers=3 --bind=0.0.0.0:9983 --log-level=debug --log-file=-
