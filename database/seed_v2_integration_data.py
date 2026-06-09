from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2

try:
    from database.init_v2_database import load_local_env
    from database.import_v2_professor_schedules import (
        DEFAULT_DOCX_PATH,
        ensure_professor_metadata_columns,
        extract_docx_paragraphs,
        parse_professor_loads,
        upsert_class as upsert_faculty_class,
        upsert_professor,
    )
    from database.create_v2_test_professor import (
        DAYS,
        TIME_SLOTS,
        TEST_EMAIL,
        TEST_PASSWORD,
        fetch_course_ids,
        upsert_class as upsert_test_class,
        upsert_room as upsert_test_room,
        upsert_test_professor,
    )
except ImportError:
    from init_v2_database import load_local_env
    from import_v2_professor_schedules import (
        DEFAULT_DOCX_PATH,
        ensure_professor_metadata_columns,
        extract_docx_paragraphs,
        parse_professor_loads,
        upsert_class as upsert_faculty_class,
        upsert_professor,
    )
    from create_v2_test_professor import (
        DAYS,
        TIME_SLOTS,
        TEST_EMAIL,
        TEST_PASSWORD,
        fetch_course_ids,
        upsert_class as upsert_test_class,
        upsert_room as upsert_test_room,
        upsert_test_professor,
    )


SAMPLE_STUDENTS = [
    ("2025103037", "Jack", "Adams"),
    ("2025103038", "Luna", "Brooks"),
    ("2025103005", "Charlie", "Brown"),
    ("2025103039", "Matthew", "Coleman"),
    ("2025103006", "Emma", "Davis"),
    ("2025103040", "Nora", "Evans"),
    ("2025103041", "Finn", "Foster"),
    ("2025103042", "Grace", "Garcia"),
    ("2025103043", "Henry", "Harris"),
    ("2025103044", "Isla", "Ibrahim"),
    ("2025103045", "Julian", "Jones"),
    ("2025103046", "Kiara", "Kim"),
    ("2025103047", "Leo", "Lopez"),
    ("2025103048", "Maya", "Mendoza"),
    ("2025103049", "Noah", "Navarro"),
    ("2025103050", "Olivia", "Ocampo"),
    ("2025103051", "Paolo", "Perez"),
    ("2025103052", "Quinn", "Quezon"),
    ("2025103053", "Rafael", "Reyes"),
    ("2025103054", "Sofia", "Santos"),
    ("2025103055", "Theo", "Tan"),
    ("2025103056", "Uma", "Uy"),
    ("2025103057", "Victor", "Valdez"),
    ("2025103058", "Willow", "Wong"),
    ("2025103059", "Xavier", "Ximenes"),
    ("2025103060", "Yara", "Yap"),
    ("2025103061", "Zion", "Zamora"),
    ("2025103062", "Ari", "Aquino"),
    ("2025103063", "Bianca", "Bautista"),
    ("2025103064", "Carlos", "Cruz"),
]


def ensure_sample_students(cursor) -> list[int]:
    student_ids: list[int] = []
    for student_number, first_name, last_name in SAMPLE_STUDENTS:
        email = f"{first_name.lower()}.{last_name.lower()}@mapua.test"
        cursor.execute(
            """
            INSERT INTO students (
                student_number, first_name, last_name, email, program, year_level, is_active
            )
            VALUES (%s, %s, %s, %s, 'BS Information Technology', '3rd Year', TRUE)
            ON CONFLICT (student_number) DO UPDATE
            SET first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                email = EXCLUDED.email,
                program = EXCLUDED.program,
                year_level = EXCLUDED.year_level,
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            RETURNING student_id
            """,
            (student_number, first_name, last_name, email),
        )
        student_ids.append(cursor.fetchone()[0])
    return student_ids


def enroll_students(cursor, student_ids: list[int], class_ids: list[int]) -> int:
    touched = 0
    for class_id in class_ids:
        cursor.execute(
            """
            SELECT UPPER(COALESCE(r.room_number, ''))
            FROM classes c
            LEFT JOIN rooms r ON r.room_id = c.room_id
            WHERE c.class_id = %s
            """,
            (class_id,),
        )
        room_row = cursor.fetchone()
        if room_row and room_row[0] == "ONLINE":
            continue

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
            touched += 1
    return touched


def seed_faculty_load(cursor, docx: Path, replace_docx_schedules: bool) -> tuple[int, int, list[int]]:
    loads = parse_professor_loads(extract_docx_paragraphs(docx))
    if not loads:
        raise RuntimeError(f"No professor schedules were parsed from {docx}.")

    ensure_professor_metadata_columns(cursor)
    if replace_docx_schedules:
        cursor.execute(
            """
            DELETE FROM attendance_sessions
            WHERE class_id IN (
                SELECT c.class_id
                FROM classes c
                JOIN professors p ON p.professor_id = c.professor_id
                WHERE p.faculty_number LIKE 'DOCX-%'
            )
            """
        )
        cursor.execute(
            """
            DELETE FROM enrollments
            WHERE class_id IN (
                SELECT c.class_id
                FROM classes c
                JOIN professors p ON p.professor_id = c.professor_id
                WHERE p.faculty_number LIKE 'DOCX-%'
            )
            """
        )
        cursor.execute(
            """
            DELETE FROM classes
            WHERE class_id IN (
                SELECT c.class_id
                FROM classes c
                JOIN professors p ON p.professor_id = c.professor_id
                WHERE p.faculty_number LIKE 'DOCX-%'
            )
            """
        )

    class_ids: list[int] = []
    for load in loads:
        professor_id = upsert_professor(cursor, load)
        for entry in load.entries:
            class_ids.append(upsert_faculty_class(cursor, professor_id, entry))
    return len(loads), len(class_ids), class_ids


def seed_test_professor(cursor) -> tuple[int, list[int]]:
    professor_id = upsert_test_professor(cursor)
    room_id = upsert_test_room(cursor)
    course_ids = fetch_course_ids(cursor)

    class_ids: list[int] = []
    for day_index, day in enumerate(DAYS):
        for slot_index, (start_time, end_time) in enumerate(TIME_SLOTS):
            course_id = course_ids[(day_index * len(TIME_SLOTS) + slot_index) % len(course_ids)]
            class_ids.append(
                upsert_test_class(
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
    return professor_id, class_ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed FRAS V2 integration testing data.")
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX_PATH)
    parser.add_argument("--replace-docx-schedules", action="store_true")
    args = parser.parse_args(argv)

    if not args.docx.exists():
        print(f"Missing DOCX file: {args.docx}")
        return 1

    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            professor_count, faculty_class_count, faculty_class_ids = seed_faculty_load(
                cursor=cursor,
                docx=args.docx,
                replace_docx_schedules=args.replace_docx_schedules,
            )
            student_ids = ensure_sample_students(cursor)
            _test_professor_id, test_class_ids = seed_test_professor(cursor)
            enrollment_count = enroll_students(cursor, student_ids, faculty_class_ids + test_class_ids)

    print(f"Imported faculty professors: {professor_count}")
    print(f"Imported faculty classes: {faculty_class_count}")
    print(f"Sample students ready: {len(SAMPLE_STUDENTS)}")
    print(f"Test professor: {TEST_EMAIL}")
    print(f"Test professor password: {TEST_PASSWORD}")
    print(f"Test professor classes: {len(test_class_ids)}")
    print(f"Enrollments touched: {enrollment_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
