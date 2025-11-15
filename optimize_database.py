#!/usr/bin/env python3
"""
Database optimization script - Add indexes and constraints
"""
import sqlite3
import os

DB_PATH = "attendance.db"

def add_indexes():
    """Add performance indexes to existing database"""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_students_number ON students(student_number)",
            "CREATE INDEX IF NOT EXISTS idx_students_email ON students(email)",
            "CREATE INDEX IF NOT EXISTS idx_enrollments_student_class ON enrollments(student_id, class_id)",
            "CREATE INDEX IF NOT EXISTS idx_classes_course_section ON classes(course_id, section)",
            "CREATE INDEX IF NOT EXISTS idx_classes_room_day_time ON classes(room_id, day_of_week, start_time)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_logs_class_date ON attendance_logs(class_id, DATE(timestamp))",
            "CREATE INDEX IF NOT EXISTS idx_attendance_logs_student_date ON attendance_logs(student_id, DATE(timestamp))",
            "CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code)",
            "CREATE INDEX IF NOT EXISTS idx_instructors_number ON instructors(instructor_number)",
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✓ Created index: {index_sql.split(' ON ')[1].split('(')[0]}")
            except Exception as e:
                print(f"✗ Failed to create index: {e}")

        conn.commit()
        print("Database optimization completed!")

if __name__ == "__main__":
    add_indexes()