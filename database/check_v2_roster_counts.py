from __future__ import annotations

import os
import sys

import psycopg2

try:
    from database.init_v2_database import load_local_env
    from database.seed_v2_integration_data import SAMPLE_STUDENTS
except ImportError:
    from init_v2_database import load_local_env
    from seed_v2_integration_data import SAMPLE_STUDENTS


def main() -> int:
    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT student_number) FROM students")
            total_students, distinct_student_numbers = cursor.fetchone()

            cursor.execute(
                """
                SELECT student_number, COUNT(*)
                FROM students
                GROUP BY student_number
                HAVING COUNT(*) > 1
                ORDER BY student_number
                """
            )
            duplicate_students = cursor.fetchall()

            cursor.execute(
                """
                SELECT student_id, class_id, COUNT(*)
                FROM enrollments
                GROUP BY student_id, class_id
                HAVING COUNT(*) > 1
                ORDER BY student_id, class_id
                LIMIT 20
                """
            )
            duplicate_enrollments = cursor.fetchall()

            sample_numbers = [student[0] for student in SAMPLE_STUDENTS]
            cursor.execute("SELECT COUNT(*) FROM students WHERE student_number = ANY(%s)", (sample_numbers,))
            managed_sample_students = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM classes c
                LEFT JOIN rooms r ON r.room_id = c.room_id
                WHERE c.is_active = TRUE
                  AND UPPER(COALESCE(r.room_number, '')) != 'ONLINE'
                """
            )
            non_online_classes = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM enrollments e
                JOIN students s ON s.student_id = e.student_id
                WHERE s.student_number = ANY(%s)
                  AND e.enrollment_status = 'active'
                """,
                (sample_numbers,),
            )
            active_sample_enrollments = cursor.fetchone()[0]

    print(f"students total: {total_students}")
    print(f"distinct student numbers: {distinct_student_numbers}")
    print(f"duplicate student numbers: {duplicate_students or 'none'}")
    print(f"duplicate enrollments: {duplicate_enrollments or 'none'}")
    print(f"managed sample students: {managed_sample_students}")
    print(f"non-online active classes: {non_online_classes}")
    print(f"active sample enrollments: {active_sample_enrollments}")
    print(f"expected if every managed sample student is enrolled in every non-online class: {non_online_classes * managed_sample_students}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
