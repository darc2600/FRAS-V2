import sqlite3
from services.db import get_connection
import random
from datetime import datetime, timedelta
import os

# Database path
DB_PATH = "attendance.db"

def generate_sample_attendance_logs():
    """Generate sample attendance logs for testing the attendance reports functionality"""

    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Please run seed_database.py first.")
        return

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if we have classes and enrollments
        cursor.execute("SELECT COUNT(*) FROM classes")
        class_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM enrollments")
        enrollment_count = cursor.fetchone()[0]

        if class_count == 0 or enrollment_count == 0:
            print("No classes or enrollments found. Please run seed_database.py first.")
            return

        print(f"Found {class_count} classes and {enrollment_count} enrollments")

        # Clear existing attendance logs
        cursor.execute("DELETE FROM attendance_logs")
        print("Cleared existing attendance logs")

        # Get all classes with their details
        cursor.execute("""
            SELECT c.class_id, c.course_id, c.instructor_id, c.room_id, c.section,
                   c.day_of_week, c.start_time, c.end_time, co.course_code, co.course_name
            FROM classes c
            JOIN courses co ON c.course_id = co.course_id
        """)
        classes = cursor.fetchall()

        # Generate attendance logs for the past 4 weeks
        today = datetime.now()
        start_date = today - timedelta(weeks=4)

        total_logs_created = 0

        for class_info in classes:
            class_id, course_id, instructor_id, room_id, section, day_of_week, start_time, end_time, course_code, course_name = class_info

            print(f"Generating attendance for {course_code} - Section {section}")

            # Get enrolled students for this class
            cursor.execute("""
                SELECT s.student_id, s.student_number, s.first_name, s.last_name
                FROM enrollments e
                JOIN students s ON e.student_id = s.student_id
                WHERE e.class_id = ?
            """, (class_id,))
            enrolled_students = cursor.fetchall()

            if not enrolled_students:
                print(f"  No students enrolled in {course_code} - Section {section}, skipping")
                continue

            print(f"  {len(enrolled_students)} students enrolled")

            # Parse day_of_week (assuming format like 'MWF' for Monday, Wednesday, Friday)
            class_days = []
            if 'M' in day_of_week: class_days.append(0)  # Monday
            if 'T' in day_of_week: class_days.append(1)  # Tuesday
            if 'W' in day_of_week: class_days.append(2)  # Wednesday
            if 'TH' in day_of_week or 'R' in day_of_week: class_days.append(3)  # Thursday
            if 'F' in day_of_week: class_days.append(4)  # Friday
            if 'S' in day_of_week: class_days.append(5)  # Saturday

            # Generate attendance for each class day in the past 4 weeks
            current_date = start_date
            while current_date <= today:
                # Check if this is a class day
                if current_date.weekday() in class_days:
                    class_date = current_date.strftime('%Y-%m-%d')

                    print(f"    Generating attendance for {class_date}")

                    # For each enrolled student, decide attendance status
                    for student in enrolled_students:
                        student_id, student_number, first_name, last_name = student

                        # Generate realistic attendance patterns
                        rand = random.random()

                        if rand < 0.75:  # 75% present
                            status_id = 1  # present
                            timestamp = generate_timestamp(class_date, start_time, 'present')
                        elif rand < 0.85:  # 10% late
                            status_id = 3  # late
                            timestamp = generate_timestamp(class_date, start_time, 'late')
                        elif rand < 0.90:  # 5% excused
                            status_id = 4  # excused
                            timestamp = generate_timestamp(class_date, start_time, 'excused')
                        else:  # 10% absent
                            status_id = 2  # absent
                            timestamp = generate_timestamp(class_date, start_time, 'absent')

                        # Insert attendance log
                        cursor.execute("""
                            INSERT INTO attendance_logs
                            (student_id, class_id, timestamp, status_id, notes)
                            VALUES (?, ?, ?, ?, ?)
                        """, (student_id, class_id, timestamp, status_id, f"Auto-generated for {class_date}"))

                        total_logs_created += 1

                current_date += timedelta(days=1)

        try:
            cursor.execute('SELECT 1')
        except Exception:
            pass

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM attendance_logs")
        total_logs = cursor.fetchone()[0]

        cursor.execute("""
            SELECT ast.status_name, COUNT(*) as count
            FROM attendance_logs al
            JOIN attendance_status_types ast ON al.status_id = ast.status_id
            GROUP BY al.status_id, ast.status_name
            ORDER BY count DESC
        """)
        status_counts = cursor.fetchall()

        print(f"\n✅ Generated {total_logs} attendance logs")
        print("Status breakdown:")
        for status, count in status_counts:
            percentage = (count / total_logs) * 100
            print(f"  {status}: {count} ({percentage:.1f}%)")

        # Show date range
        cursor.execute("SELECT MIN(date(timestamp)), MAX(date(timestamp)) FROM attendance_logs")
        date_range = cursor.fetchone()
        print(f"Date range: {date_range[0]} to {date_range[1]}")

        # Show sample logs
        print("\nSample attendance logs:")
        cursor.execute("""
            SELECT s.first_name, s.last_name, c.course_code, date(al.timestamp), time(al.timestamp), ast.status_name
            FROM attendance_logs al
            JOIN students s ON al.student_id = s.student_id
            JOIN classes cl ON al.class_id = cl.class_id
            JOIN courses c ON cl.course_id = c.course_id
            JOIN attendance_status_types ast ON al.status_id = ast.status_id
            ORDER BY al.timestamp DESC, s.last_name
            LIMIT 10
        """)
        sample_logs = cursor.fetchall()

        for log in sample_logs:
            first_name, last_name, course_code, date, time, status = log
            print(f"  {last_name}, {first_name} - {course_code} - {date} {time} - {status}")

def generate_timestamp(class_date, start_time, status):
    """Generate a realistic timestamp based on class date, start time, and attendance status"""
    # Parse start_time (format: HH:MM)
    hours, minutes = map(int, start_time.split(':'))

    if status == 'present':
        # Students arrive 0-15 minutes early or up to 5 minutes late
        variation_minutes = random.randint(-15, 5)
    elif status == 'late':
        # Late students arrive 5-30 minutes after start
        variation_minutes = random.randint(5, 30)
    elif status == 'excused':
        # Excused students might not have a specific time, use class start time
        variation_minutes = 0
    else:  # absent
        # Absent students don't have a timestamp, but we'll still create one for the record
        variation_minutes = 0

    class_datetime = datetime.strptime(f"{class_date} {start_time}", '%Y-%m-%d %H:%M')
    attendance_time = class_datetime + timedelta(minutes=variation_minutes)

    return attendance_time.strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    print("Generating sample attendance logs...")
    generate_sample_attendance_logs()
    print("Done!")