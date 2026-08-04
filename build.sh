#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Pré-aquece os caches a partir das fontes oficiais no Supabase.
python manage.py refresh_data --force
python manage.py refresh_schools --force