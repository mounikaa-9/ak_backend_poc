#!/bin/bash
# Navigate to src directory where manage.py is
cd src
# Install Python dependencies
pip install -r ../requirements.txt
# Collect static files
python manage.py collectstatic --noinput --clear