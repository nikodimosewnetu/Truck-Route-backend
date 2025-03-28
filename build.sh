#!/bin/bash
# Exit on error
set -o errexit

# Create static files directory if it doesn't exist
mkdir -p staticfiles

# Collect static files
python manage.py collectstatic --noinput

# Apply migrations (if you have a database)
# python manage.py migrate