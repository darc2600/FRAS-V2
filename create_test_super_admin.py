#!/usr/bin/env python3
"""
Script to create a new super admin user for testing
"""

import sqlite3
import os
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

def create_test_super_admin():
    """Create a test super admin user"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Test data
            email = "test.superadmin@fras.com"
            password = "super123"
            first_name = "Test"
            last_name = "SuperAdmin"

            # Check if already exists
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                print(f"❌ Super admin {email} already exists!")
                return

            # Create super admin record
            cursor.execute("""
                INSERT INTO super_admins (employee_number, last_name, first_name, email, dept_id, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (f"SUPER{secrets.token_hex(4).upper()}", last_name, first_name, email, 1))

            super_admin_id = cursor.lastrowid

            # Create user record
            cursor.execute("""
                INSERT INTO users (email, password, role, reference_id, created_at)
                VALUES (?, ?, 'super_admin', ?, CURRENT_TIMESTAMP)
            """, (email, password, super_admin_id))

            conn.commit()

            print("✅ Test Super Admin Created Successfully!")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   Full Name: {first_name} {last_name}")
            print("\nYou can now login with these credentials to test super admin features.")

    except Exception as e:
        print(f"❌ Error creating super admin: {e}")

if __name__ == "__main__":
    create_test_super_admin()