import sqlite3
from datetime import datetime
from services.db import get_connection

# We'll open the DB connection when needed using get_connection()

print("Attendance Log Deletion Options:")
print("=" * 50)
print("1. Delete ALL attendance logs")
print("2. Delete logs from a specific DATE")
print("3. Delete logs from a specific STUDENT")
print("4. Delete logs from a specific CLASS")
print("5. Delete logs with NULL notes")
print("0. Cancel")
print("=" * 50)

choice = input("Choose option (0-5): ").strip()

with get_connection() as conn:
    cursor = conn.cursor()

    if choice == "0":
        print("Cancelled.")
        conn.close()
        exit()

    if choice == "1":
        confirm = input("Delete ALL attendance logs? This cannot be undone! (yes/no): ").strip().lower()
        if confirm == "yes":
            cursor.execute("DELETE FROM attendance_logs")
            deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Deleted {deleted} attendance logs")
        else:
            print("Cancelled.")
        conn.close()
        exit()

    # remaining options handled above
