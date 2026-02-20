#!/usr/bin/env python3
"""
Script to create a new Super Admin user in FRAS database
Usage: python add_superadmin.py "email@example.com" "FirstName" "LastName" "password123"
"""

import sqlite3
import sys
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

def add_super_admin(email, first_name, last_name, password, employee_number=None):
    """Create a new super admin user"""

    if not employee_number:
        # Generate employee number
        employee_number = f"SUPER{hash(email) % 10000:04d}"

    # For now, use plain text password (same as test users)
    hashed_password = password

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print(f"❌ Error: Email '{email}' already exists!")
            return False

        # Check if employee number already exists
        cursor.execute("SELECT super_admin_id FROM super_admins WHERE employee_number = ?", (employee_number,))
        if cursor.fetchone():
            print(f"❌ Error: Employee number '{employee_number}' already exists!")
            return False

        # Get a default department (use first available)
        cursor.execute("SELECT dept_id FROM departments LIMIT 1")
        dept_result = cursor.fetchone()
        dept_id = dept_result[0] if dept_result else 1

        # 1. Insert into super_admins table first
        cursor.execute("""
            INSERT INTO super_admins (employee_number, last_name, first_name, email, dept_id, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (employee_number, last_name, first_name, email, dept_id))

        super_admin_id = cursor.lastrowid
        print(f"✅ Created super admin record with ID: {super_admin_id}")

        # 2. Insert into users table for authentication
        cursor.execute("""
            INSERT INTO users (email, password, role, reference_id, created_at)
            VALUES (?, ?, 'super_admin', ?, CURRENT_TIMESTAMP)
        """, (email, hashed_password, super_admin_id))

        user_id = cursor.lastrowid
        print(f"✅ Created user authentication record with ID: {user_id}")

        conn.commit()
        print(f"\n🎉 Super Admin created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {first_name} {last_name}")
        print(f"   Employee Number: {employee_number}")
        print(f"   Password: {password}")
        print(f"\n⚠️  IMPORTANT: Save these credentials securely!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating super admin: {e}")
        return False

    finally:
        conn.close()

def main():
    if len(sys.argv) < 5:
        print("Usage: python add_superadmin.py <email> <first_name> <last_name> <password> [employee_number]")
        print("\nExample:")
        print('python add_superadmin.py "admin@university.edu" "John" "Doe" "securepass123"')
        print('python add_superadmin.py "admin@university.edu" "John" "Doe" "securepass123" "SUPER001"')
        sys.exit(1)

    email = sys.argv[1]
    first_name = sys.argv[2]
    last_name = sys.argv[3]
    password = sys.argv[4]
    employee_number = sys.argv[5] if len(sys.argv) > 5 else None

    print("🔐 Creating new Super Admin...")
    print(f"   Email: {email}")
    print(f"   Name: {first_name} {last_name}")
    print(f"   Employee Number: {employee_number or '(auto-generated)'}")

    success = add_super_admin(email, first_name, last_name, password, employee_number)

    if success:
        print("\n✅ Super Admin account created successfully!")
        print("You can now log in with these credentials.")
    else:
        print("\n❌ Failed to create Super Admin account.")
        sys.exit(1)

if __name__ == "__main__":
    main()