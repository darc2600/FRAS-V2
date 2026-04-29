#!/usr/bin/env python3
"""
FRAS Demo Data Reset
====================

Rebuilds a clean, presentation-ready SQLite demo dataset for the Facial
Recognition Attendance System.

Default behavior:
  - Uses attendance.db in the project root.
  - Creates a timestamped backup before changing data.
  - Clears demo rows from the main FRAS tables.
  - Recreates deterministic demo departments, users, students, instructors,
    rooms, classes, enrollments, attendance logs, support tickets, permissions,
    and settings.

Usage:
  python scripts/reset_demo_data.py
  python scripts/reset_demo_data.py --db attendance.db --no-backup
  python scripts/reset_demo_data.py --db /path/to/attendance.db
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "attendance.db"
MANILA_NOW = datetime.now()

DEMO_PASSWORD = "DemoPass123!"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    if not table_exists(cur, table):
        return False
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def add_column_if_missing(cur: sqlite3.Cursor, table: str, column: str, definition: str) -> None:
    if table_exists(cur, table) and not column_exists(cur, table, column):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def safe_execute(cur: sqlite3.Cursor, sql: str, params: Sequence | None = None) -> None:
    try:
        cur.execute(sql, params or [])
    except sqlite3.OperationalError as exc:
        print(f"[WARN] Skipped SQL because the current schema does not support it: {exc}")


def make_password_hash(password: str) -> str:
    """Return a passlib-compatible-ish hash when passlib exists, otherwise PBKDF2 text.

    The existing FRAS code has used passlib bcrypt/pbkdf2 in different places. This
    function prefers passlib when it is installed so demo accounts work with the
    current authentication flow. The hashlib fallback is still deterministic and
    safer than storing plaintext for local demo data.
    """
    try:
        from passlib.hash import bcrypt  # type: ignore

        return bcrypt.hash(password)
    except Exception:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return "pbkdf2_sha256$120000$" + salt.hex() + "$" + digest.hex()


def create_schema(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS departments (
            dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_code VARCHAR(20) UNIQUE,
            dept_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_number VARCHAR(20) UNIQUE,
            last_name TEXT,
            first_name TEXT,
            email TEXT,
            face_data_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS instructors (
            instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_number VARCHAR(20) UNIQUE,
            last_name TEXT,
            first_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            dept_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
        );

        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_number TEXT UNIQUE,
            last_name TEXT,
            first_name TEXT,
            email TEXT,
            dept_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
        );

        CREATE TABLE IF NOT EXISTS it_admins (
            it_admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_number VARCHAR(20) UNIQUE,
            last_name TEXT,
            first_name TEXT,
            email TEXT UNIQUE,
            dept_id INTEGER REFERENCES departments(dept_id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS super_admins (
            super_admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_number VARCHAR(20) UNIQUE,
            last_name TEXT,
            first_name TEXT,
            email TEXT UNIQUE,
            dept_id INTEGER REFERENCES departments(dept_id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT,
            reference_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code VARCHAR(20) UNIQUE,
            course_name VARCHAR(100),
            units INTEGER,
            dept_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
        );

        CREATE TABLE IF NOT EXISTS room_types (
            room_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name VARCHAR(50) UNIQUE
        );

        CREATE TABLE IF NOT EXISTS attendance_status_types (
            status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_code VARCHAR(20) UNIQUE NOT NULL,
            status_name VARCHAR(50) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS campuses (
            campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campus_name TEXT UNIQUE NOT NULL,
            location TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS buildings (
            building_id INTEGER PRIMARY KEY AUTOINCREMENT,
            building_name TEXT NOT NULL,
            campus_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(campus_id) REFERENCES campuses(campus_id),
            UNIQUE(building_name, campus_id)
        );

        CREATE TABLE IF NOT EXISTS rooms (
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
        );

        CREATE TABLE IF NOT EXISTS school_terms (
            term_id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_year VARCHAR(20),
            term INTEGER,
            start_date DATE,
            end_date DATE
        );

        CREATE TABLE IF NOT EXISTS classes (
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
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            class_id INTEGER,
            enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(class_id) REFERENCES classes(class_id)
        );

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
        );

        CREATE TABLE IF NOT EXISTS student_face_embeddings (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            embedding_json TEXT NOT NULL,
            source_image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, model_name)
        );

        CREATE TABLE IF NOT EXISTS permissions (
            permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            permission_code TEXT UNIQUE NOT NULL,
            permission_name TEXT NOT NULL,
            description TEXT,
            category TEXT
        );

        CREATE TABLE IF NOT EXISTS role_permissions (
            user_type TEXT NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (user_type, permission_id)
        );

        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT,
            setting_type TEXT,
            updated_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            assigned_to INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ticket_replies (
            reply_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_internal BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    add_column_if_missing(cur, "users", "is_active", "INTEGER DEFAULT 1")
    add_column_if_missing(cur, "students", "face_data_path", "TEXT")
    add_column_if_missing(cur, "attendance_logs", "updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    add_column_if_missing(cur, "support_tickets", "assigned_to", "INTEGER")


def clear_demo_data(cur: sqlite3.Cursor) -> None:
    tables = [
        "ticket_replies",
        "support_tickets",
        "student_face_embeddings",
        "attendance_logs",
        "enrollments",
        "classes",
        "school_terms",
        "rooms",
        "buildings",
        "campuses",
        "room_types",
        "attendance_status_types",
        "courses",
        "users",
        "super_admins",
        "it_admins",
        "admins",
        "instructors",
        "students",
        "role_permissions",
        "permissions",
        "system_settings",
        "departments",
    ]
    for table in tables:
        if table_exists(cur, table):
            cur.execute(f"DELETE FROM {table}")
            safe_execute(cur, "DELETE FROM sqlite_sequence WHERE name = ?", (table,))


def insert_many(cur: sqlite3.Cursor, sql: str, rows: Iterable[Sequence]) -> None:
    cur.executemany(sql, list(rows))


def seed_reference_data(cur: sqlite3.Cursor) -> None:
    insert_many(
        cur,
        "INSERT INTO departments (dept_code, dept_name) VALUES (?, ?)",
        [
            ("CS", "Computer Science Department"),
            ("IT", "Information Technology Department"),
            ("CE", "Computer Engineering Department"),
            ("GEN", "General Education Department"),
        ],
    )

    insert_many(
        cur,
        "INSERT INTO room_types (type_name) VALUES (?)",
        [("Lecture Room",), ("Computer Laboratory",), ("Engineering Laboratory",)],
    )

    insert_many(
        cur,
        """
        INSERT INTO attendance_status_types (status_code, status_name, description, is_active)
        VALUES (?, ?, ?, 1)
        """,
        [
            ("present", "Present", "Student was recognized within the expected attendance window."),
            ("late", "Late", "Student was recognized after the configured grace period."),
            ("absent", "Absent", "Student was not recognized during the class session."),
            ("excused", "Excused", "Student absence was excused by the instructor."),
        ],
    )

    insert_many(
        cur,
        "INSERT INTO campuses (campus_name, location) VALUES (?, ?)",
        [("Main Campus", "Intramuros, Manila")],
    )

    insert_many(
        cur,
        "INSERT INTO buildings (building_name, campus_id) VALUES (?, ?)",
        [("North Building", 1), ("South Building", 1), ("Innovation Center", 1)],
    )

    insert_many(
        cur,
        """
        INSERT INTO rooms (room_number, floor_level, campus_id, building_id, room_type_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("201", 2, 1, 1, 1),
            ("305", 3, 1, 1, 2),
            ("407", 4, 1, 2, 1),
            ("512", 5, 1, 2, 2),
            ("LAB-1", 1, 1, 3, 3),
            ("LAB-2", 1, 1, 3, 2),
        ],
    )

    insert_many(
        cur,
        """
        INSERT INTO courses (course_code, course_name, units, dept_id)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("CS101", "Introduction to Computing", 3, 1),
            ("CS204", "Data Structures and Algorithms", 3, 1),
            ("IT210", "Web Systems and Technologies", 3, 2),
            ("IT320", "Database Management Systems", 3, 2),
            ("CPE301", "Embedded Systems", 4, 3),
            ("GEN101", "Professional Ethics", 2, 4),
        ],
    )

    current_year = MANILA_NOW.year
    insert_many(
        cur,
        "INSERT INTO school_terms (school_year, term, start_date, end_date) VALUES (?, ?, ?, ?)",
        [
            (f"{current_year}-{current_year + 1}", 1, f"{current_year}-01-08", f"{current_year}-05-31"),
            (f"{current_year}-{current_year + 1}", 2, f"{current_year}-06-10", f"{current_year}-10-20"),
        ],
    )


def seed_people_and_users(cur: sqlite3.Cursor) -> None:
    password_hash = make_password_hash(DEMO_PASSWORD)

    admin_profiles = [
        ("SA-0001", "Reyes", "Andrea", "superadmin@fras.demo", 2),
        ("IT-0001", "Santos", "Miguel", "itadmin@fras.demo", 2),
    ]

    cur.execute(
        """
        INSERT INTO super_admins (employee_number, last_name, first_name, email, dept_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        admin_profiles[0],
    )
    super_admin_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO it_admins (employee_number, last_name, first_name, email, dept_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        admin_profiles[1],
    )
    it_admin_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO admins (employee_number, last_name, first_name, email, dept_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("ADM-0001", "Cruz", "Patricia", "admin@fras.demo", 2),
    )
    legacy_admin_id = cur.lastrowid

    instructors = [
        ("INS-0001", "Garcia", "Elena", "elena.garcia@fras.demo", password_hash, 1),
        ("INS-0002", "Dela Cruz", "Marco", "marco.delacruz@fras.demo", password_hash, 2),
        ("INS-0003", "Lim", "Hannah", "hannah.lim@fras.demo", password_hash, 3),
        ("INS-0004", "Torres", "Nathan", "nathan.torres@fras.demo", password_hash, 4),
    ]
    insert_many(
        cur,
        """
        INSERT INTO instructors (instructor_number, last_name, first_name, email, password, dept_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        instructors,
    )

    cur.execute("SELECT instructor_id, email FROM instructors ORDER BY instructor_id")
    instructor_rows = cur.fetchall()

    user_rows = [
        ("superadmin@fras.demo", password_hash, "super_admin", super_admin_id, 1),
        ("itadmin@fras.demo", password_hash, "it_admin", it_admin_id, 1),
        ("admin@fras.demo", password_hash, "admin", legacy_admin_id, 1),
    ]
    user_rows.extend((row["email"], password_hash, "instructor", row["instructor_id"], 1) for row in instructor_rows)

    insert_many(
        cur,
        """
        INSERT INTO users (email, password, role, reference_id, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        user_rows,
    )

    first_names = [
        "Alyssa", "Bianca", "Carlo", "Dianne", "Ethan", "Frances", "Gabriel", "Hazel",
        "Ivan", "Jasmine", "Kyle", "Lara", "Miguel", "Nina", "Oscar", "Paula", "Quinn",
        "Rafael", "Sophia", "Theo", "Uma", "Victor", "Wendy", "Xander", "Yna", "Zach",
        "Aria", "Bryce", "Celine", "Derek", "Elaine", "Felix", "Gina", "Harvey", "Iris",
        "Jonas", "Kara", "Leo", "Mika", "Noel", "Olivia", "Patrick", "Ria", "Sean",
        "Trixie", "Uriel", "Vera", "Wyatt",
    ]
    last_names = [
        "Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Mendoza", "Torres", "Flores",
        "Rivera", "Ramos", "Aquino", "Castillo",
    ]
    students = []
    for index in range(1, 121):
        first = first_names[(index - 1) % len(first_names)]
        last = last_names[(index - 1) % len(last_names)]
        student_number = f"2026{index:04d}"
        face_path = f"dataset/{student_number}" if index <= 92 else None
        created_at = datetime(MANILA_NOW.year, ((index - 1) % 12) + 1, min(((index - 1) % 25) + 1, 25), 9, 0)
        students.append(
            (
                student_number,
                last,
                first,
                f"{first.lower()}.{last.lower()}{index}@students.fras.demo",
                face_path,
                created_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

    insert_many(
        cur,
        """
        INSERT INTO students (student_number, last_name, first_name, email, face_data_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        students,
    )

    # Simulated embeddings for students with completed face registration.
    cur.execute("SELECT student_id, student_number, face_data_path FROM students WHERE face_data_path IS NOT NULL")
    embedding_rows = [
        (row["student_id"], "demo-face-model-v1", "[0.012,0.338,0.557,0.774]", f"{row['face_data_path']}/sample_01.jpg")
        for row in cur.fetchall()
    ]
    insert_many(
        cur,
        """
        INSERT INTO student_face_embeddings (student_id, model_name, embedding_json, source_image_path)
        VALUES (?, ?, ?, ?)
        """,
        embedding_rows,
    )


def seed_classes_attendance(cur: sqlite3.Cursor) -> None:
    class_rows = [
        (1, 2, 1, "A", "Monday", "08:00", "09:30", 1),
        (2, 5, 1, "B", "Tuesday", "10:00", "11:30", 1),
        (3, 3, 2, "A", "Wednesday", "13:00", "14:30", 1),
        (4, 4, 2, "C", "Thursday", "15:00", "16:30", 1),
        (5, 6, 3, "A", "Friday", "09:00", "11:00", 1),
        (6, 1, 4, "D", "Saturday", "08:00", "10:00", 1),
    ]
    insert_many(
        cur,
        """
        INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time, term_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        class_rows,
    )

    enrollments = []
    for class_id in range(1, 7):
        start = ((class_id - 1) * 20) + 1
        student_ids = list(range(start, min(start + 28, 121)))
        if class_id == 6:
            student_ids = list(range(1, 31))
        for student_id in student_ids:
            enrollments.append((student_id, class_id))
    insert_many(
        cur,
        "INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)",
        enrollments,
    )

    cur.execute("SELECT status_id, status_code FROM attendance_status_types")
    status_map = {row["status_code"]: row["status_id"] for row in cur.fetchall()}

    attendance_rows = []
    today = datetime(MANILA_NOW.year, min(MANILA_NOW.month, 12), 20, 8, 0)
    for month in range(1, 13):
        for class_id in range(1, 7):
            cur.execute("SELECT student_id FROM enrollments WHERE class_id=? ORDER BY student_id LIMIT 18", (class_id,))
            students = [row["student_id"] for row in cur.fetchall()]
            for offset, student_id in enumerate(students):
                session_date = datetime(MANILA_NOW.year, month, min(5 + ((class_id + offset) % 20), 25), 8 + (class_id % 6), offset % 60)
                if session_date > today + timedelta(days=30):
                    continue
                if offset % 11 == 0:
                    status = "absent"
                elif offset % 7 == 0:
                    status = "late"
                elif offset % 17 == 0:
                    status = "excused"
                else:
                    status = "present"
                attendance_rows.append(
                    (
                        student_id,
                        class_id,
                        session_date.strftime("%Y-%m-%d %H:%M:%S"),
                        status_map[status],
                        "Seeded demo attendance record",
                    )
                )

    insert_many(
        cur,
        """
        INSERT INTO attendance_logs (student_id, class_id, timestamp, status_id, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        attendance_rows,
    )


def seed_permissions_settings_support(cur: sqlite3.Cursor) -> None:
    permissions = [
        ("view_own_schedule", "View Own Schedule", "View personal teaching schedule.", "schedule"),
        ("view_attendance_logs", "View Attendance Logs", "View student attendance records.", "attendance"),
        ("mark_attendance", "Mark Attendance", "Use facial recognition attendance capture.", "attendance"),
        ("register_students", "Register Students", "Register student profiles and face data.", "registration"),
        ("manage_users", "Manage Users", "Add, update, and deactivate users.", "user_management"),
        ("reset_passwords", "Reset Passwords", "Reset user credentials.", "user_management"),
        ("manage_rooms_schedule", "Manage Rooms and Schedule", "Configure rooms, classes, and schedules.", "administration"),
        ("view_analytics", "View Analytics", "View system analytics and reports.", "analytics"),
        ("system_admin", "System Administration", "Full system administration access.", "administration"),
    ]
    insert_many(
        cur,
        """
        INSERT INTO permissions (permission_code, permission_name, description, category)
        VALUES (?, ?, ?, ?)
        """,
        permissions,
    )

    role_permissions = {
        "instructor": ["view_own_schedule", "view_attendance_logs", "mark_attendance", "register_students"],
        "it_admin": [
            "view_own_schedule",
            "view_attendance_logs",
            "mark_attendance",
            "register_students",
            "manage_users",
            "reset_passwords",
            "manage_rooms_schedule",
            "view_analytics",
        ],
        "super_admin": [code for code, *_ in permissions],
    }
    for role, codes in role_permissions.items():
        for code in codes:
            cur.execute("SELECT permission_id FROM permissions WHERE permission_code=?", (code,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    "INSERT INTO role_permissions (user_type, permission_id) VALUES (?, ?)",
                    (role, row["permission_id"]),
                )

    settings = [
        ("system_name", "FRAS - Facial Recognition Attendance System", "config"),
        ("version", "1.0.0-demo", "config"),
        ("maintenance_mode", "false", "config"),
        ("face_recognition_threshold", "0.60", "config"),
        ("session_timeout", "3600", "config"),
        ("backup_frequency", "daily", "config"),
        ("demo_dataset", "true", "config"),
        ("last_demo_reset", MANILA_NOW.strftime("%Y-%m-%d %H:%M:%S"), "audit"),
    ]
    insert_many(
        cur,
        "INSERT INTO system_settings (setting_key, setting_value, setting_type) VALUES (?, ?, ?)",
        settings,
    )

    cur.execute("SELECT user_id FROM users WHERE email='superadmin@fras.demo'")
    super_user_id = cur.fetchone()["user_id"]
    cur.execute("SELECT user_id FROM users WHERE email='itadmin@fras.demo'")
    it_user_id = cur.fetchone()["user_id"]
    cur.execute("SELECT user_id FROM users WHERE role='instructor' ORDER BY user_id LIMIT 1")
    instructor_user_id = cur.fetchone()["user_id"]

    tickets = [
        (
            instructor_user_id,
            "Face registration camera check",
            "Camera preview works locally but needs verification before the panel demo.",
            "technical",
            "medium",
            "open",
            it_user_id,
            days_ago(6),
        ),
        (
            instructor_user_id,
            "Attendance report export review",
            "Please verify that CSV, Excel, and PDF exports match the filtered class report.",
            "attendance",
            "high",
            "in_progress",
            it_user_id,
            days_ago(4),
        ),
        (
            super_user_id,
            "Add analytics explanation text",
            "Panel requested clearer wording for face registration completion metrics.",
            "feature",
            "medium",
            "resolved",
            it_user_id,
            days_ago(2),
        ),
        (
            instructor_user_id,
            "Room schedule duplicate validation",
            "Schedule editor should reject duplicate room records during room creation.",
            "technical",
            "critical",
            "open",
            it_user_id,
            days_ago(1),
        ),
    ]
    insert_many(
        cur,
        """
        INSERT INTO support_tickets
        (user_id, subject, description, category, priority, status, assigned_to, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tickets,
    )

    cur.execute("SELECT ticket_id FROM support_tickets WHERE status='resolved' LIMIT 1")
    resolved_ticket = cur.fetchone()
    if resolved_ticket:
        cur.execute(
            """
            INSERT INTO ticket_replies (ticket_id, user_id, message, is_internal, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (
                resolved_ticket["ticket_id"],
                it_user_id,
                "Updated analytics labels to use Face Registration Completion instead of technical embedding wording.",
                days_ago(1),
            ),
        )


def days_ago(days: int) -> str:
    return (MANILA_NOW - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def print_summary(cur: sqlite3.Cursor) -> None:
    print("\nDemo data summary")
    print("-----------------")
    for table in [
        "users",
        "students",
        "instructors",
        "rooms",
        "classes",
        "enrollments",
        "attendance_logs",
        "student_face_embeddings",
        "support_tickets",
    ]:
        if table_exists(cur, table):
            cur.execute(f"SELECT COUNT(*) AS count FROM {table}")
            print(f"{table:28s} {cur.fetchone()['count']}")

    print("\nDemo accounts")
    print("-------------")
    print("superadmin@fras.demo   / DemoPass123!")
    print("itadmin@fras.demo      / DemoPass123!")
    print("elena.garcia@fras.demo / DemoPass123!")
    print("marco.delacruz@fras.demo / DemoPass123!")


def reset_demo_data(db_path: Path, create_backup: bool = True) -> None:
    db_path = db_path.resolve()
    if create_backup and db_path.exists():
        backup_dir = PROJECT_ROOT / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{db_path.stem}_before_demo_reset_{timestamp}{db_path.suffix}"
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")

    with connect(db_path) as conn:
        cur = conn.cursor()
        print(f"Resetting demo data in: {db_path}")
        create_schema(cur)
        clear_demo_data(cur)
        seed_reference_data(cur)
        seed_people_and_users(cur)
        seed_classes_attendance(cur)
        seed_permissions_settings_support(cur)
        conn.commit()
        print_summary(cur)

    print("\nDone. Restart the backend after running this script.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset FRAS SQLite database with clean demo data.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to SQLite database. Default: attendance.db")
    parser.add_argument("--no-backup", action="store_true", help="Do not create a timestamped backup before reset.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reset_demo_data(Path(args.db), create_backup=not args.no_backup)


if __name__ == "__main__":
    main()
