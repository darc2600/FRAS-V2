import sqlite3
from datetime import datetime

# Open with timeout to handle locked database
conn = sqlite3.connect('attendance.db', timeout=30.0)
cursor = conn.cursor()

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

if choice == "0":
    print("Cancelled.")
    conn.close()
    exit()

elif choice == "1":
    confirm = input("Delete ALL attendance logs? This cannot be undone! (yes/no): ").strip().lower()
    if confirm == "yes":
        cursor.execute("DELETE FROM attendance_logs")
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ Deleted {deleted} attendance logs")
    else:
        print("Cancelled.")

elif choice == "2":
    date_str = input("Enter date to delete (YYYY-MM-DD): ").strip()
    try:
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM attendance_logs WHERE DATE(timestamp) = ?", (date_str,))
        count = cursor.fetchone()[0]
        confirm = input(f"Delete {count} logs from {date_str}? (yes/no): ").strip().lower()
        if confirm == "yes":
            cursor.execute("DELETE FROM attendance_logs WHERE DATE(timestamp) = ?", (date_str,))
            deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Deleted {deleted} attendance logs from {date_str}")
        else:
            print("Cancelled.")
    except ValueError:
        print("❌ Invalid date format")

elif choice == "3":
    student_id = input("Enter student_id to delete: ").strip()
    cursor.execute("SELECT COUNT(*) FROM attendance_logs WHERE student_id = ?", (student_id,))
    count = cursor.fetchone()[0]
    if count == 0:
        print(f"❌ No logs found for student {student_id}")
    else:
        confirm = input(f"Delete {count} logs for student {student_id}? (yes/no): ").strip().lower()
        if confirm == "yes":
            cursor.execute("DELETE FROM attendance_logs WHERE student_id = ?", (student_id,))
            deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Deleted {deleted} attendance logs for student {student_id}")
        else:
            print("Cancelled.")

elif choice == "4":
    class_id = input("Enter class_id to delete: ").strip()
    cursor.execute("SELECT COUNT(*) FROM attendance_logs WHERE class_id = ?", (class_id,))
    count = cursor.fetchone()[0]
    if count == 0:
        print(f"❌ No logs found for class {class_id}")
    else:
        confirm = input(f"Delete {count} logs for class {class_id}? (yes/no): ").strip().lower()
        if confirm == "yes":
            cursor.execute("DELETE FROM attendance_logs WHERE class_id = ?", (class_id,))
            deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Deleted {deleted} attendance logs for class {class_id}")
        else:
            print("Cancelled.")

elif choice == "5":
    cursor.execute("SELECT COUNT(*) FROM attendance_logs WHERE notes IS NULL")
    count = cursor.fetchone()[0]
    if count == 0:
        print("✅ No logs with NULL notes found")
    else:
        confirm = input(f"Delete {count} logs with NULL notes? (yes/no): ").strip().lower()
        if confirm == "yes":
            cursor.execute("DELETE FROM attendance_logs WHERE notes IS NULL")
            deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Deleted {deleted} attendance logs with NULL notes")
        else:
            print("Cancelled.")

else:
    print("❌ Invalid choice")

conn.close()
