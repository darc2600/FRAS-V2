from __future__ import annotations

import os
import sys
from datetime import datetime

import psycopg2

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env


TEST_EMAIL = "test.professor@mapua.test"
TEST_PASSWORD = "password"
TEST_FACULTY_NUMBER = "TEST-001"
TEST_FIRST_NAME = "Testing"
TEST_LAST_NAME = "Professor"
TEST_ROOM = "TEST-LAB"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_SLOTS = [
    ("07:00", "08:10"),
    ("08:10", "09:20"),
    ("09:20", "10:30"),
    ("10:30", "11:40"),
    ("11:40", "12:50"),
    ("12:50", "14:00"),
    ("14:00", "15:10"),
    ("15:10", "16:20"),
    ("16:20", "17:30"),
    ("17:30", "18:40"),
    ("18:40", "19:50"),
    ("19:50", "21:00"),
]


def fetch_course_ids(cursor) -> list[int]:
    cursor.execute("SELECT course_id FROM courses ORDER BY course_code")
    course_ids = [row[0] for row in cursor.fetchall()]
    if course_ids:
        return course_ids

    seed_courses = [
        ("TEST101", "Testing Course 101"),
        ("TEST102", "Testing Course 102"),
        ("TEST103", "Testing Course 103"),
    ]
    for code, name in seed_courses:
        cursor.execute(
            """
            INSERT INTO courses (course_code, course_name, units)
            VALUES (%s, %s, 3)
            ON CONFLICT (course_code) DO UPDATE
            SET course_name = EXCLUDED.course_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (code, name),
        )
    cursor.execute("SELECT course_id FROM courses ORDER BY course_code")
    return [row[0] for row in cursor.fetchall()]


def upsert_test_professor(cursor) -> int:
    cursor.execute(
        """
        INSERT INTO users (email, password_hash, role)
        VALUES (%s, %s, 'professor')
        ON CONFLICT (email) DO UPDATE
        SET password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            is_active = TRUE,
            updated_at = CURRENT_TIMESTAMP
        RETURNING user_id
        """,
        (TEST_EMAIL, TEST_PASSWORD),
    )
    user_id = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO professors (
            user_id, faculty_number, first_name, last_name, email,
            employment_status, total_units, lecture_units, lab_units
        )
        VALUES (%s, %s, %s, %s, %s, 'Testing', 84, 42, 42)
        ON CONFLICT (faculty_number) DO UPDATE
        SET user_id = EXCLUDED.user_id,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            email = EXCLUDED.email,
            employment_status = EXCLUDED.employment_status,
            total_units = EXCLUDED.total_units,
            lecture_units = EXCLUDED.lecture_units,
            lab_units = EXCLUDED.lab_units,
            updated_at = CURRENT_TIMESTAMP
        RETURNING professor_id
        """,
        (user_id, TEST_FACULTY_NUMBER, TEST_FIRST_NAME, TEST_LAST_NAME, TEST_EMAIL),
    )
    return cursor.fetchone()[0]


def upsert_room(cursor) -> int:
    cursor.execute(
        """
        INSERT INTO rooms (room_number, floor_level, building)
        VALUES (%s, 0, 'Testing')
        ON CONFLICT (room_number) DO UPDATE
        SET building = EXCLUDED.building,
            updated_at = CURRENT_TIMESTAMP
        RETURNING room_id
        """,
        (TEST_ROOM,),
    )
    return cursor.fetchone()[0]


def upsert_class(cursor, professor_id: int, room_id: int, course_id: int, day: str, slot_index: int, start_time: str, end_time: str) -> int:
    section = f"T{DAYS.index(day) + 1:01d}{slot_index + 1:02d}"
    cursor.execute(
        """
        SELECT class_id
        FROM classes
        WHERE professor_id = %s
          AND section = %s
          AND day_of_week = %s
          AND start_time = %s
          AND end_time = %s
        """,
        (professor_id, section, day, start_time, end_time),
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE classes
            SET course_id = %s,
                room_id = %s,
                term = 'TEST',
                academic_year = '2025-2026',
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE class_id = %s
            RETURNING class_id
            """,
            (course_id, room_id, existing[0]),
        )
        return cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO classes (
            course_id, professor_id, room_id, section, day_of_week,
            start_time, end_time, term, academic_year, is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'TEST', '2025-2026', TRUE)
        RETURNING class_id
        """,
        (course_id, professor_id, room_id, section, day, start_time, end_time),
    )
    return cursor.fetchone()[0]


def enroll_existing_students(cursor, class_id: int) -> int:
    cursor.execute("SELECT student_id FROM students WHERE is_active = TRUE ORDER BY student_number")
    student_ids = [row[0] for row in cursor.fetchall()]
    for student_id in student_ids:
        cursor.execute(
            """
            INSERT INTO enrollments (student_id, class_id, enrollment_status)
            VALUES (%s, %s, 'active')
            ON CONFLICT (student_id, class_id) DO UPDATE
            SET enrollment_status = 'active',
                updated_at = CURRENT_TIMESTAMP
            """,
            (student_id, class_id),
        )
    return len(student_ids)


def main() -> int:
    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            professor_id = upsert_test_professor(cursor)
            room_id = upsert_room(cursor)
            course_ids = fetch_course_ids(cursor)

            cursor.execute(
                """
                UPDATE classes
                SET is_active = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE professor_id = %s
                  AND term = 'TEST'
                """,
                (professor_id,),
            )

            class_ids: list[int] = []
            for day_index, day in enumerate(DAYS):
                for slot_index, (start_time, end_time) in enumerate(TIME_SLOTS):
                    course_id = course_ids[(day_index * len(TIME_SLOTS) + slot_index) % len(course_ids)]
                    class_ids.append(
                        upsert_class(
                            cursor=cursor,
                            professor_id=professor_id,
                            room_id=room_id,
                            course_id=course_id,
                            day=day,
                            slot_index=slot_index,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )

            enrollment_count = 0
            for class_id in class_ids:
                enrollment_count += enroll_existing_students(cursor, class_id)

    print(f"Created test professor: {TEST_EMAIL}")
    print(f"Password: {TEST_PASSWORD}")
    print(f"Classes: {len(DAYS) * len(TIME_SLOTS)}")
    print(f"Enrollments touched: {enrollment_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
