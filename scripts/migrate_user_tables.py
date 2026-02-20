#!/usr/bin/env python3
"""
Database migration to restructure user tables for FRAS
Creates separate data tables for different user types and unified users table for authentication
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

def migrate_user_tables():
    """Migrate to new user table structure"""

    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Starting user table migration...")

        # Create new tables
        print("Creating it_admins table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS it_admins (
                it_admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_number VARCHAR(20) UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT UNIQUE,
                dept_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
            )
        ''')

        print("Creating super_admins table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS super_admins (
                super_admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_number VARCHAR(20) UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT UNIQUE,
                dept_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
            )
        ''')

        # Update instructors table (remove password and user_type columns)
        print("Updating instructors table...")
        try:
            cursor.execute("ALTER TABLE instructors DROP COLUMN password")
        except sqlite3.OperationalError:
            pass  # Column might not exist

        try:
            cursor.execute("ALTER TABLE instructors DROP COLUMN user_type")
        except sqlite3.OperationalError:
            pass  # Column might not exist

        # Update admins table (remove password and user_type columns)
        print("Updating admins table...")
        try:
            cursor.execute("ALTER TABLE admins DROP COLUMN password")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE admins DROP COLUMN user_type")
        except sqlite3.OperationalError:
            pass

        # Update users table structure
        print("Updating users table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_new (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('instructor', 'it_admin', 'super_admin')),
                reference_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Migrate existing data
        print("Migrating existing data...")

        # Migrate instructors
        cursor.execute("SELECT instructor_id, email FROM instructors")
        instructors = cursor.fetchall()
        for instructor_id, email in instructors:
            # Check if user already exists
            cursor.execute("SELECT user_id FROM users_new WHERE email = ?", (email,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users_new (email, password, role, reference_id)
                    VALUES (?, ?, 'instructor', ?)
                """, (email, 'password123', instructor_id))  # Default password

        # Migrate admins to it_admins
        cursor.execute("SELECT admin_id, employee_number, last_name, first_name, email, dept_id FROM admins")
        admins = cursor.fetchall()
        for admin_id, emp_num, lname, fname, email, dept_id in admins:
            # Insert into it_admins table
            cursor.execute("""
                INSERT INTO it_admins (employee_number, last_name, first_name, email, dept_id)
                VALUES (?, ?, ?, ?, ?)
            """, (emp_num, lname, fname, email, dept_id))
            it_admin_id = cursor.lastrowid

            # Create user entry
            cursor.execute("""
                INSERT INTO users_new (email, password, role, reference_id)
                VALUES (?, ?, 'it_admin', ?)
            """, (email, 'admin123', it_admin_id))

        # Create a default super admin
        cursor.execute("""
            INSERT INTO super_admins (employee_number, last_name, first_name, email, dept_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('SUPER001', 'Super', 'Admin', 'superadmin@fras.com', 1))
        super_admin_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users_new (email, password, role, reference_id)
            VALUES (?, ?, 'super_admin', ?)
        """, ('superadmin@fras.com', 'super123', super_admin_id))

        # Replace old users table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # Update permissions
        print("Updating permissions...")
        cursor.execute("DELETE FROM permissions")  # Clear existing
        cursor.execute("DELETE FROM role_permissions")  # Clear existing

        # Insert new permissions
        permissions = [
            ('view_own_schedule', 'View personal schedule', 'schedule'),
            ('view_attendance_logs', 'View attendance logs', 'attendance'),
            ('mark_attendance', 'Mark attendance using facial recognition', 'attendance'),
            ('register_students', 'Register new students', 'registration'),
            ('manage_users', 'Create and manage user accounts', 'user_management'),
            ('manage_rooms_schedule', 'Edit room and schedule configurations', 'administration'),
            ('system_admin', 'Full system administration access', 'administration'),
            ('view_analytics', 'View system analytics and reports', 'analytics'),
            ('manage_content', 'Manage system content and settings', 'content')
        ]

        cursor.executemany("""
            INSERT INTO permissions (permission_name, description, category)
            VALUES (?, ?, ?)
        """, permissions)

        # Assign permissions to roles
        role_permissions = [
            # Instructor permissions
            ('instructor', 'view_own_schedule'),
            ('instructor', 'view_attendance_logs'),
            ('instructor', 'mark_attendance'),
            ('instructor', 'register_students'),

            # IT Admin permissions (all instructor + additional)
            ('it_admin', 'view_own_schedule'),
            ('it_admin', 'view_attendance_logs'),
            ('it_admin', 'mark_attendance'),
            ('it_admin', 'register_students'),
            ('it_admin', 'manage_users'),
            ('it_admin', 'manage_rooms_schedule'),
            ('it_admin', 'view_analytics'),

            # Super Admin permissions (all permissions)
            ('super_admin', 'view_own_schedule'),
            ('super_admin', 'view_attendance_logs'),
            ('super_admin', 'mark_attendance'),
            ('super_admin', 'register_students'),
            ('super_admin', 'manage_users'),
            ('super_admin', 'manage_rooms_schedule'),
            ('super_admin', 'system_admin'),
            ('super_admin', 'view_analytics'),
            ('super_admin', 'manage_content')
        ]

        for role, perm_name in role_permissions:
            cursor.execute("""
                INSERT INTO role_permissions (user_type, permission_id)
                SELECT ?, permission_id FROM permissions WHERE permission_name = ?
            """, (role, perm_name))

        conn.commit()
        print("✅ Migration completed successfully!")

        # Show summary
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        roles = cursor.fetchall()
        print("\nUser counts by role:")
        for role, count in roles:
            print(f"  {role}: {count}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    migrate_user_tables()