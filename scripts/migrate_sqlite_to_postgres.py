"""
Migrate SQLite (attendance.db) to PostgreSQL.

Usage:
  - Install dependencies: pip install -r requirements.txt
  - Set DATABASE_URL env var, e.g.:
      export DATABASE_URL=postgresql://username:password@host:5432/dbname
    On Windows PowerShell:
      $env:DATABASE_URL = 'postgresql://username:password@host:5432/dbname'

  - Run:
      python scripts/migrate_sqlite_to_postgres.py --sqlite-file attendance.db

Notes:
 - This script creates tables in Postgres mirroring the schema in backend.py
 - It copies rows in an order that respects foreign keys
 - It does not attempt to migrate triggers. After migration you can enable triggers on the Postgres side as needed.
 - Test on a non-production Postgres first.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from typing import Any, Dict, List, Tuple

import psycopg2
from psycopg2.extras import execute_values

SQLITE_DEFAULT = 'attendance.db'


POSTGRES_TABLES_DDL = [
    """
    CREATE TABLE IF NOT EXISTS students (
        student_id SERIAL PRIMARY KEY,
        student_number VARCHAR(20) UNIQUE,
        last_name TEXT,
        first_name TEXT,
        email TEXT,
        face_data_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS instructors (
        instructor_id SERIAL PRIMARY KEY,
        last_name TEXT,
        first_name TEXT,
        email TEXT,
        department TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS courses (
        course_code VARCHAR(20) PRIMARY KEY,
        course_name VARCHAR(100),
        units INTEGER,
        department TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS rooms (
        room_id VARCHAR(20) PRIMARY KEY,
        floor_level INTEGER,
        room_number VARCHAR(10),
        building_name VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS classes (
        class_id VARCHAR(20) PRIMARY KEY,
        course_code VARCHAR(20),
        room_id VARCHAR(20),
        instructor_id INTEGER,
        section VARCHAR(10),
        day_of_week VARCHAR(10),
        start_time TIME,
        end_time TIME,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id SERIAL PRIMARY KEY,
        student_id INTEGER,
        class_id VARCHAR(20),
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS attendance_logs (
        log_id SERIAL PRIMARY KEY,
        student_id INTEGER,
        class_id VARCHAR(20),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
]


def get_sqlite_rows(sqlite_conn: sqlite3.Connection, table: str) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    cur = sqlite_conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return cols, rows


def copy_table(sqlite_conn: sqlite3.Connection, pg_conn, table: str, mapping: Dict[str, str] | None = None):
    """Copy rows from sqlite table to Postgres table.

    mapping: optional dict mapping sqlite column -> postgres column (if names differ)
    """
    cols, rows = get_sqlite_rows(sqlite_conn, table)
    if not rows:
        print(f"{table}: no rows to copy")
        return
    pg_cols = [mapping.get(c, c) if mapping else c for c in cols]
    placeholders = ','.join(['%s'] * len(pg_cols))
    insert_sql = f"INSERT INTO {table} ({', '.join(pg_cols)}) VALUES %s"
    with pg_conn.cursor() as cur:
        try:
            execute_values(cur, insert_sql, rows)
            pg_conn.commit()
            print(f"Copied {len(rows)} rows into {table}")
        except Exception as e:
            pg_conn.rollback()
            print(f"Failed copying into {table}: {e}")
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description='Migrate attendance.db (SQLite) to Postgres')
    parser.add_argument('--sqlite-file', default=SQLITE_DEFAULT, help='Path to SQLite file')
    parser.add_argument('--database-url', default=os.environ.get('DATABASE_URL'), help='Postgres DATABASE_URL (env DATABASE_URL)')
    args = parser.parse_args(argv)

    if not args.database_url:
        print('Please provide --database-url or set DATABASE_URL env var')
        sys.exit(2)

    if not os.path.exists(args.sqlite_file):
        print(f"SQLite file not found: {args.sqlite_file}")
        sys.exit(2)

    sqlite_conn = sqlite3.connect(args.sqlite_file)
    # Use row factory to preserve order

    print('Connecting to Postgres...')
    pg_conn = psycopg2.connect(args.database_url)

    # Create tables
    with pg_conn.cursor() as cur:
        for ddl in POSTGRES_TABLES_DDL:
            cur.execute(ddl)
        pg_conn.commit()
    print('Created/verified tables in Postgres')

    # Copy order: students, instructors, courses, rooms, classes, enrollments, attendance_logs
    order = ['students', 'instructors', 'courses', 'rooms', 'classes', 'enrollments', 'attendance_logs']

    # Special handling: sqlite may have autoincrement integers and column names, ensure mapping if needed
    for table in order:
        # if the sqlite DB doesn't have the table, skip
        try:
            copy_table(sqlite_conn, pg_conn, table)
        except sqlite3.OperationalError as e:
            print(f"Skipping {table} (not present in sqlite): {e}")

    print('Migration complete. Verify data and recreate any triggers/indexes as needed on Postgres.')


if __name__ == '__main__':
    main()
