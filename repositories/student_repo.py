from services.db import get_connection


class StudentRepository:
    def add_student(self, student_number, last_name, first_name, email, face_data_path=None):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO students (student_number, last_name, first_name, email, face_data_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_number, last_name, first_name, email, face_data_path))
            conn.commit()
            try:
                return cursor.lastrowid
            except Exception:
                # psycopg2 uses cursor.rowcount and other properties; return None if unavailable
                return None

    def get_student_by_id(self, student_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
            return cursor.fetchone()

    def get_student_by_number(self, student_number):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE student_number = ?', (student_number,))
            return cursor.fetchone()

    def update_student(self, student_id, **kwargs):
        with get_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [student_id]
            cursor.execute(f'UPDATE students SET {fields} WHERE student_id = ?', values)
            conn.commit()

    def delete_student(self, student_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
            conn.commit()
