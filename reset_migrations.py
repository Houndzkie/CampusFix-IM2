"""
Clears all Django migration history records from django_migrations table in Supabase,
then we can run migrate fresh. Run with:
  venv2\Scripts\python.exe reset_migrations.py
"""
import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # List what's currently applied
    cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name;")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} migration records:")
    for r in rows:
        print(f"  {r[0]}.{r[1]}")

    confirm = input("\nDelete ALL migration history records? (yes/no): ").strip().lower()
    if confirm == "yes":
        cursor.execute("DELETE FROM django_migrations;")
        print("✓ All migration history cleared. Now run: python manage.py migrate")
    else:
        print("Aborted.")
