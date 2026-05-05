import sqlite3
from services.db import get_connection

DB_PATH = "attendance.db"


def _is_postgres_backend():
    import os
    db_url = (os.environ.get("DATABASE_URL") or "").strip().lower()
    return bool(db_url) and not db_url.startswith("sqlite")

class EnrollmentRepository:
    def add_enrollment(self, student_id, class_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            if _is_postgres_backend():
                cursor.execute('''
                    INSERT INTO enrollments (student_id, class_id)
                    VALUES (?, ?)
                    RETURNING enrollment_id
                ''', (student_id, class_id))
                row = cursor.fetchone()
                conn.commit()
                return row[0] if row else None

            cursor.execute('''
                INSERT INTO enrollments (student_id, class_id)
                VALUES (?, ?)
            ''', (student_id, class_id))
            conn.commit()
            return cursor.lastrowid

    def get_enrollments_by_student(self, student_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM enrollments WHERE student_id = ?', (student_id,))
            return cursor.fetchall()

    def get_enrollments_by_class(self, class_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM enrollments WHERE class_id = ?', (class_id,))
            return cursor.fetchall()

    def delete_enrollment(self, enrollment_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM enrollments WHERE enrollment_id = ?', (enrollment_id,))
            conn.commit()
