from pathlib import Path
import argparse
import json
import os
import sqlite3
import sys

import psycopg2
from psycopg2.extras import Json

try:
    from database.init_v2_database import load_local_env
except ImportError:
    from init_v2_database import load_local_env


ROOT_DIR = Path(__file__).resolve().parents[1]
V1_DB_PATH = ROOT_DIR / "attendance.db"
SOURCE_CLASS_ID = 8


def fetch_one(cursor, sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchone()


def fetch_all(cursor, sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchall()


def split_day_of_week(value: str) -> str:
    value = (value or "").strip()
    if value:
        return value
    return "Monday"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reset V2 from one V1 class snapshot.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Truncate V2 tables before seeding from V1. This deletes existing V2 seed data.",
    )
    args = parser.parse_args(argv)
    if not args.force:
        print("Refusing to seed from V1 because this script truncates V2 tables.")
        print("Run with --force only when you intentionally want to replace current V2 data.")
        return 2

    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    if not V1_DB_PATH.exists():
        print(f"Missing source database: {V1_DB_PATH}")
        return 1

    source = sqlite3.connect(V1_DB_PATH)
    source.row_factory = sqlite3.Row
    source_cursor = source.cursor()

    class_row = fetch_one(
        source_cursor,
        """
        SELECT
            c.class_id,
            c.section,
            c.day_of_week,
            c.start_time,
            c.end_time,
            co.course_code,
            co.course_name,
            co.units,
            r.room_number,
            r.floor_level,
            b.building_name,
            i.instructor_number,
            i.first_name AS professor_first_name,
            i.last_name AS professor_last_name,
            i.email AS professor_email
        FROM classes c
        JOIN courses co ON co.course_id = c.course_id
        LEFT JOIN rooms r ON r.room_id = c.room_id
        LEFT JOIN buildings b ON b.building_id = r.building_id
        LEFT JOIN instructors i ON i.instructor_id = c.instructor_id
        WHERE c.class_id = ?
        """,
        (SOURCE_CLASS_ID,),
    )
    if not class_row:
        print(f"Source class {SOURCE_CLASS_ID} was not found.")
        return 1

    students = fetch_all(
        source_cursor,
        """
        SELECT
            s.student_id,
            s.student_number,
            s.first_name,
            s.last_name,
            s.email,
            s.face_data_path
        FROM enrollments e
        JOIN students s ON s.student_id = e.student_id
        WHERE e.class_id = ?
        ORDER BY s.last_name, s.first_name, s.student_number
        """,
        (SOURCE_CLASS_ID,),
    )

    embeddings = {
        row["student_id"]: row
        for row in fetch_all(
            source_cursor,
            """
            SELECT student_id, model_name, embedding_json, source_image_path
            FROM student_face_embeddings
            WHERE student_id IN (
                SELECT student_id FROM enrollments WHERE class_id = ?
            )
            """,
            (SOURCE_CLASS_ID,),
        )
    }

    with psycopg2.connect(database_url) as target:
        with target.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE
                    blackboard_sync_logs,
                    professor_overrides,
                    attendance_events,
                    student_session_records,
                    attendance_sessions,
                    student_face_profiles,
                    enrollments,
                    classes,
                    rooms,
                    courses,
                    students,
                    professors,
                    users,
                    attendance_status_types
                RESTART IDENTITY CASCADE
                """
            )

            cursor.execute(
                """
                INSERT INTO attendance_status_types (status_name)
                VALUES ('present'), ('late'), ('absent'), ('excused'), ('partial')
                """
            )

            professor_email = class_row["professor_email"] or "professor@mapua.edu.ph"
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, role)
                VALUES (%s, %s, 'professor')
                RETURNING user_id
                """,
                (professor_email, "dev-password-change-me"),
            )
            user_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO professors (
                    user_id, faculty_number, first_name, last_name, email
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING professor_id
                """,
                (
                    user_id,
                    class_row["instructor_number"],
                    class_row["professor_first_name"] or "Professor",
                    class_row["professor_last_name"] or "Sample",
                    professor_email,
                ),
            )
            professor_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO courses (course_code, course_name, units)
                VALUES (%s, %s, %s)
                RETURNING course_id
                """,
                (
                    class_row["course_code"],
                    class_row["course_name"],
                    class_row["units"] or 3,
                ),
            )
            course_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO rooms (room_number, floor_level, building)
                VALUES (%s, %s, %s)
                RETURNING room_id
                """,
                (
                    class_row["room_number"] or "TBA",
                    class_row["floor_level"],
                    class_row["building_name"] or "Main",
                ),
            )
            room_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO classes (
                    course_id, professor_id, room_id, section, day_of_week,
                    start_time, end_time, term, academic_year
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING class_id
                """,
                (
                    course_id,
                    professor_id,
                    room_id,
                    class_row["section"],
                    split_day_of_week(class_row["day_of_week"]),
                    class_row["start_time"],
                    class_row["end_time"],
                    "1",
                    "2026-2027",
                ),
            )
            class_id = cursor.fetchone()[0]

            for student in students:
                cursor.execute(
                    """
                    INSERT INTO students (
                        student_number, first_name, last_name, email, program, year_level
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING student_id
                    """,
                    (
                        student["student_number"],
                        student["first_name"] or "Student",
                        student["last_name"] or "Sample",
                        student["email"],
                        "BS Information Technology",
                        "3rd Year",
                    ),
                )
                student_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO enrollments (student_id, class_id)
                    VALUES (%s, %s)
                    """,
                    (student_id, class_id),
                )

                embedding = embeddings.get(student["student_id"])
                if embedding or student["face_data_path"]:
                    embedding_json = None
                    if embedding and embedding["embedding_json"]:
                        embedding_json = Json(json.loads(embedding["embedding_json"]))
                    cursor.execute(
                        """
                        INSERT INTO student_face_profiles (
                            student_id, face_image_path, embedding_json, model_name
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            student_id,
                            (embedding["source_image_path"] if embedding else None)
                            or student["face_data_path"],
                            embedding_json,
                            embedding["model_name"] if embedding else None,
                        ),
                    )

    source.close()
    print(
        f"Seeded FRAS V2 with {class_row['course_code']} {class_row['section']} "
        f"and {len(students)} enrolled students."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
