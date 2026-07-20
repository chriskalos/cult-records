#!/usr/bin/env bash
set -o errexit

python -m pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py migrate_media_to_cloudinary --clear-missing
