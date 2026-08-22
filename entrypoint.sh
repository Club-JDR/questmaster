#!/bin/sh
set -e
export FLASK_APP=questmaster:create_app
flask db upgrade
flask seed-trophies
exec gunicorn --workers=2 --threads=4 --max-requests=1000 --max-requests-jitter=100 --bind 0.0.0.0:8000 questmaster:app