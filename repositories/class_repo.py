import sqlite3
from services.db import get_connection

DB_PATH = "attendance.db"

class ClassRepository:
    def add_class(self, class_id, course_code, room_id, instructor_id, section, day_of_week, start_time, end_time):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO classes (class_id, course_code, room_id, instructor_id, section, day_of_week, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (class_id, course_code, room_id, instructor_id, section, day_of_week, start_time, end_time))
            conn.commit()
            return class_id

    def get_class(self, class_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
            return cursor.fetchone()

    def update_class(self, class_id, **kwargs):
        with get_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [class_id]
            cursor.execute(f'UPDATE classes SET {fields} WHERE class_id = ?', values)
            conn.commit()

    def delete_class(self, class_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM classes WHERE class_id = ?', (class_id,))
            conn.commit()
