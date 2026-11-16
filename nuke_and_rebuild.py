"""
Nuclear reset: drops all tables in the 'public' schema of Supabase and
rebuilds them from scratch with Django's migrate.

CAUTION: This destroys ALL existing data.
Run: venv2\Scripts\python.exe nuke_and_rebuild.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Get all user tables in public schema
    cursor.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Found {len(tables)} tables:")
    for t in tables:
        print(f"  {t}")

    if not tables:
        print("No tables found. Run migrate directly.")
        sys.exit(0)

    confirm = input("\nDROP ALL these tables? This deletes all data. (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        sys.exit(0)

    # Drop all with CASCADE
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
        print(f"  Dropped: {table}")

    print("\nAll tables dropped. Now run: venv2\\Scripts\\python.exe manage.py migrate")
