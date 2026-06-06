import os
import sys

import psycopg2

from init_v2_database import load_local_env


def main() -> int:
    load_local_env()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM professors")
            professor_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM courses")
            course_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM rooms")
            room_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM classes")
            class_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM students")
            student_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM enrollments")
            enrollment_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM student_face_profiles")
            face_profile_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT
                    c.class_id,
                    co.course_code,
                    co.course_name,
                    c.section,
                    c.day_of_week,
                    c.start_time,
                    c.end_time,
                    r.room_number,
                    p.first_name,
                    p.last_name
                FROM classes c
                JOIN courses co ON co.course_id = c.course_id
                JOIN rooms r ON r.room_id = c.room_id
                JOIN professors p ON p.professor_id = c.professor_id
                ORDER BY c.class_id
                """
            )
            classes = cursor.fetchall()

    print(f"professors: {professor_count}")
    print(f"courses: {course_count}")
    print(f"rooms: {room_count}")
    print(f"classes: {class_count}")
    print(f"students: {student_count}")
    print(f"enrollments: {enrollment_count}")
    print(f"student_face_profiles: {face_profile_count}")
    print("classes:")
    for row in classes:
        print(
            f"- #{row[0]} {row[1]} {row[3]} | {row[2]} | {row[4]} "
            f"{row[5]}-{row[6]} | Room {row[7]} | Prof. {row[8]} {row[9]}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
