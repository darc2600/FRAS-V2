#!/usr/bin/env python3
"""
Script to create a test admin user for authentication testing
"""
import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

def create_test_admin():
    """Create a test admin user with known credentials"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check if test admin already exists
            cursor.execute("SELECT admin_id FROM admins WHERE email = ?", ("testadmin@fras.com",))
            if cursor.fetchone():
                print("Test admin already exists")
                return

            # Use plaintext password for testing (auth system supports both)
            password = "admin123"

            # Create test admin
            cursor.execute("""
                INSERT INTO admins (email, password, user_type, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, ("testadmin@fras.com", password, "super_admin"))

            conn.commit()
            print(f"Created test admin: testadmin@fras.com / {password}")

    except Exception as e:
        print(f"Error creating test admin: {e}")

if __name__ == "__main__":
    create_test_admin()