import sqlite3
from services.db import get_connection

DB_PATH = "attendance.db"


def _is_postgres_backend():
    import os
    db_url = (os.environ.get("DATABASE_URL") or "").strip().lower()
    return bool(db_url) and not db_url.startswith("sqlite")

class InstructorRepository:
    def add_instructor(self, instructor_number, last_name, first_name, email, department):
        with get_connection() as conn:
            cursor = conn.cursor()
            if _is_postgres_backend():
                cursor.execute('''
                    INSERT INTO instructors (instructor_number, last_name, first_name, email, dept_id)
                    VALUES (?, ?, ?, ?, ?)
                    RETURNING instructor_id
                ''', (instructor_number, last_name, first_name, email, department))
                row = cursor.fetchone()
                conn.commit()
                return row[0] if row else None

            cursor.execute('''
                INSERT INTO instructors (instructor_number, last_name, first_name, email, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (instructor_number, last_name, first_name, email, department))
            conn.commit()
            return cursor.lastrowid

    def get_instructor_by_id(self, instructor_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM instructors WHERE instructor_id = ?', (instructor_id,))
            return cursor.fetchone()

    def update_instructor(self, instructor_id, **kwargs):
        with get_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [instructor_id]
            cursor.execute(f'UPDATE instructors SET {fields} WHERE instructor_id = ?', values)
            conn.commit()

    def delete_instructor(self, instructor_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM instructors WHERE instructor_id = ?', (instructor_id,))
            conn.commit()
