Migration scripts
=================

This folder contains utilities to migrate your local SQLite database (`attendance.db`) to a Postgres database (e.g. Amazon RDS).

Prerequisites
 - Python 3.10+
 - Install dependencies: `pip install -r ../requirements.txt`
 - A reachable Postgres instance and a `DATABASE_URL` (e.g. `postgresql://user:pass@host:5432/dbname`)
 - Backup your `attendance.db` before running migration

Running the migration

From the repository root:

```bash
# On Windows PowerShell, set environment variable like:
# $env:DATABASE_URL = 'postgresql://username:password@host:5432/dbname'
python scripts/migrate_sqlite_to_postgres.py --sqlite-file attendance.db
```

Notes
 - The script creates matching tables in Postgres and copies rows. It does not recreate triggers.
 - After migration, point your backend to Postgres by setting `DATABASE_URL` and updating DB access code (or swap sqlite3 calls for psycopg2/SQLAlchemy). I can help with backend wiring if you want.
