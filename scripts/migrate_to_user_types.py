#!/usr/bin/env python3
"""
Migration script to assign user types to existing users
Phase 1: User Types System Implementation
"""

import sqlite3
import os

DB_PATH = "attendance.db"

def migrate_user_types():
    """Assign appropriate user types to existing users"""

    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Update existing students to regular users
        cursor.execute("UPDATE students SET user_type = 'regular' WHERE user_type IS NULL OR user_type = ''")
        students_updated = cursor.rowcount
        print(f"Updated {students_updated} students to 'regular' user type")

        # Update existing instructors to regular users (they can be promoted to it_admin later)
        cursor.execute("UPDATE instructors SET user_type = 'regular' WHERE user_type IS NULL OR user_type = ''")
        instructors_updated = cursor.rowcount
        print(f"Updated {instructors_updated} instructors to 'regular' user type")

        # Update existing admins to super_admin
        cursor.execute("UPDATE admins SET user_type = 'super_admin' WHERE user_type IS NULL OR user_type = ''")
        admins_updated = cursor.rowcount
        print(f"Updated {admins_updated} admins to 'super_admin' user type")

        # Update users table with user_type if needed
        cursor.execute("UPDATE users SET user_type = 'regular' WHERE user_type IS NULL OR user_type = ''")
        users_updated = cursor.rowcount
        print(f"Updated {users_updated} users table records")

        # Verify the changes
        print("\nVerification:")
        cursor.execute("SELECT user_type, COUNT(*) FROM students GROUP BY user_type")
        results = cursor.fetchall()
        for user_type, count in results:
            print(f"Students - {user_type}: {count}")

        cursor.execute("SELECT user_type, COUNT(*) FROM instructors GROUP BY user_type")
        results = cursor.fetchall()
        for user_type, count in results:
            print(f"Instructors - {user_type}: {count}")

        cursor.execute("SELECT user_type, COUNT(*) FROM admins GROUP BY user_type")
        results = cursor.fetchall()
        for user_type, count in results:
            print(f"Admins - {user_type}: {count}")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    migrate_user_types()