#!/usr/bin/env bash
# Render build script
set -o errexit

pip install pipenv
pipenv install --system --deploy

python manage.py collectstatic --no-input
python manage.py migrate
