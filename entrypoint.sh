#!/bin/sh
set -e
flask db upgrade
flask seed-trophies
exec gunicorn --workers=2 --threads=4 --bind 0.0.0.0:8000 questmaster:app