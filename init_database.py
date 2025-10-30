#!/usr/bin/env python3
"""
Database initialization script for FRAS
Creates the complete database schema from scratch
Run this after adding attendance.db to .gitignore
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = "attendance.db"

def init_database():
    """Create the complete database schema"""

    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        print(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)

    print(f"Creating new database: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # STUDENTS
        cursor.execute('''
            CREATE TABLE students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number VARCHAR(20) UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT,
                face_data_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # INSTRUCTORS
        cursor.execute('''
            CREATE TABLE instructors (
                instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instructor_number VARCHAR(20) UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT,
                dept_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
            )
        ''')

        # COURSES
        cursor.execute('''
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code VARCHAR(20) UNIQUE,
                course_name VARCHAR(100),
                units INTEGER,
                dept_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
            )
        ''')

        # DEPARTMENTS
        cursor.execute('''
            CREATE TABLE departments (
                dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_code VARCHAR(20) UNIQUE,
                dept_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ROOM_TYPES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_types (
                room_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name VARCHAR(50) UNIQUE
            )
        ''')

        # ATTENDANCE_STATUS_TYPES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_status_types (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_code VARCHAR(20) UNIQUE NOT NULL,
                status_name VARCHAR(50) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # CAMPUSES
        cursor.execute('''
            CREATE TABLE campuses (
                campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                campus_name TEXT UNIQUE NOT NULL,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # BUILDINGS
        cursor.execute('''
            CREATE TABLE buildings (
                building_id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_name TEXT NOT NULL,
                campus_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(campus_id) REFERENCES campuses(campus_id),
                UNIQUE(building_name, campus_id)
            )
        ''')

        # ROOMS
        cursor.execute('''
            CREATE TABLE rooms (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number VARCHAR(20),
                floor_level INTEGER,
                campus_id INTEGER NOT NULL,
                building_id INTEGER,
                room_type_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(campus_id) REFERENCES campuses(campus_id),
                FOREIGN KEY(building_id) REFERENCES buildings(building_id),
                FOREIGN KEY(room_type_id) REFERENCES room_types(room_type_id)
            )
        ''')

        # SCHOOL_TERMS
        cursor.execute('''
            CREATE TABLE school_terms (
                term_id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_year VARCHAR(20),
                term INTEGER,
                start_date DATE,
                end_date DATE
            )
        ''')

        # CLASSES
        cursor.execute('''
            CREATE TABLE classes (
                class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                room_id INTEGER,
                instructor_id INTEGER,
                section VARCHAR(10),
                day_of_week VARCHAR(10),
                start_time TIME,
                end_time TIME,
                term_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(course_id) REFERENCES courses(course_id),
                FOREIGN KEY(room_id) REFERENCES rooms(room_id),
                FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id),
                FOREIGN KEY(term_id) REFERENCES school_terms(term_id)
            )
        ''')

        # ENROLLMENTS
        cursor.execute('''
            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                class_id INTEGER,
                enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(class_id) REFERENCES classes(class_id)
            )
        ''')

        # ATTENDANCE_LOGS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                class_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status_id INTEGER,
                notes TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(class_id) REFERENCES classes(class_id),
                FOREIGN KEY(status_id) REFERENCES attendance_status_types(status_id)
            )
        ''')

        # Triggers to auto-update updated_at on row update
        tables_to_trigger = [
            'students', 'instructors', 'courses', 'departments', 'room_types',
            'attendance_status_types', 'campuses', 'buildings', 'rooms', 'school_terms', 'classes',
            'enrollments', 'attendance_logs'
        ]

        for table in tables_to_trigger:
            cursor.execute(f'''
                CREATE TRIGGER IF NOT EXISTS trg_{table}_updated_at
                AFTER UPDATE ON {table}
                FOR EACH ROW
                BEGIN
                    UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid;
                END;
            ''')

        conn.commit()
        print("Database schema created successfully!")

def create_indexes():
    """Create database indexes for performance"""
    print("Creating database indexes...")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_students_number ON students(student_number);",
            "CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);",
            "CREATE INDEX IF NOT EXISTS idx_enrollments_student_class ON enrollments(student_id, class_id);",
            "CREATE INDEX IF NOT EXISTS idx_classes_course_section ON classes(course_id, section);",
            "CREATE INDEX IF NOT EXISTS idx_classes_room_day_time ON classes(room_id, day_of_week, start_time);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_logs_class_date ON attendance_logs(class_id, DATE(timestamp));",
            "CREATE INDEX IF NOT EXISTS idx_attendance_logs_student_date ON attendance_logs(student_id, DATE(timestamp));",
            "CREATE INDEX IF NOT EXISTS idx_attendance_logs_status ON attendance_logs(status_id);",
            "CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(course_code);",
            "CREATE INDEX IF NOT EXISTS idx_instructors_number ON instructors(instructor_number);"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        print("Database indexes created successfully!")

if __name__ == "__main__":
    print("Initializing FRAS database...")
    init_database()
    create_indexes()
    print("\nDatabase initialization complete!")
    print("Run 'python seed_database.py' to populate with sample data")