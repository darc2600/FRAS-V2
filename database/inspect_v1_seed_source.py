import sqlite3


def main() -> int:
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

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
            i.instructor_number,
            i.first_name,
            i.last_name,
            COUNT(e.student_id) AS student_count
        FROM classes c
        JOIN courses co ON co.course_id = c.course_id
        LEFT JOIN rooms r ON r.room_id = c.room_id
        LEFT JOIN instructors i ON i.instructor_id = c.instructor_id
        LEFT JOIN enrollments e ON e.class_id = c.class_id
        GROUP BY
            c.class_id, co.course_code, co.course_name, c.section,
            c.day_of_week, c.start_time, c.end_time, r.room_number,
            i.instructor_number, i.first_name, i.last_name
        ORDER BY student_count DESC, c.class_id
        LIMIT 10
        """
    )

    print("Candidate classes:")
    for row in cursor.fetchall():
        print(row)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
