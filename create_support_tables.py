#!/usr/bin/env python3
"""
Create support ticket tables in the database
"""

import sqlite3
import os

DB_PATH = "attendance.db"
SCHEMA_PATH = "database/support_tickets_schema.sql"

def create_support_tables():
    """Create support ticket tables"""

    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    if not os.path.exists(SCHEMA_PATH):
        print(f"Schema file {SCHEMA_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()

        cursor.executescript(schema_sql)
        conn.commit()

        print("✅ Support ticket tables created successfully!")

        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'support_%'")
        tables = cursor.fetchall()
        print(f"Created tables: {[table[0] for table in tables]}")

    except Exception as e:
        print(f"❌ Failed to create support tables: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    create_support_tables()