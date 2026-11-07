#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Setting up TCU Thesis Library for GitHub Live Demo..."
echo "=========================================================="

# Install Python requirements
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run migrations and seed sample database
python seed_demo_data.py

# Collect static files
python manage.py collectstatic --noinput || true

echo "=========================================================="
echo " TCU Thesis Library is Ready!"
echo " Server will start automatically on port 8000."
echo ""
echo " Demo Logins:"
echo "   • Admin:     admin     / admin12345"
echo "   • Librarian: librarian / librarian12345"
echo "   • Professor: professor / professor12345"
echo "   • Student:   student   / student12345"
echo "=========================================================="
