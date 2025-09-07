import sqlite3

DB_PATH = "attendance.db"

class StudentRepository:
    def add_student(self, student_number, last_name, first_name, email, face_data_path=None):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO students (student_number, last_name, first_name, email, face_data_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_number, last_name, first_name, email, face_data_path))
            conn.commit()
            return cursor.lastrowid

    def get_student_by_id(self, student_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
            return cursor.fetchone()

    def get_student_by_number(self, student_number):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE student_number = ?', (student_number,))
            return cursor.fetchone()

    def update_student(self, student_id, **kwargs):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [student_id]
            cursor.execute(f'UPDATE students SET {fields} WHERE student_id = ?', values)
            conn.commit()

    def delete_student(self, student_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
            conn.commit()
