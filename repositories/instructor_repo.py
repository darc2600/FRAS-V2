import sqlite3
from services.db import get_connection

DB_PATH = "attendance.db"

class InstructorRepository:
    def add_instructor(self, instructor_number, last_name, first_name, email, department):
        with get_connection() as conn:
            cursor = conn.cursor()
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
