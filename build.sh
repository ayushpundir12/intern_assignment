#!/usr/bin/env bash
# exit on error
set -o errexit

# Go to backend directory
cd backend

# Install dependencies
pip install -r ../requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Seed database with demo users
python seed_data.py
