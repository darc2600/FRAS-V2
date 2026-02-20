#!/usr/bin/env python3
"""
Create complete database schema from SQL file
"""

import sqlite3
import os

DB_PATH = "attendance.db"
SCHEMA_PATH = "database/complete_schema.sql"

def create_complete_schema():
    """Create all tables from the complete schema SQL file"""

    if not os.path.exists(SCHEMA_PATH):
        print(f"Schema file {SCHEMA_PATH} not found!")
        return

    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        print(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)

    print(f"Creating database from schema: {SCHEMA_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # Read and execute the complete schema
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()

        cursor.executescript(schema_sql)
        conn.commit()

        print("✅ Complete database schema created successfully!")

if __name__ == "__main__":
    create_complete_schema()