import sqlite3

DB_PATH = "attendance.db"

class InstructorRepository:
    def add_instructor(self, last_name, first_name, email, department):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO instructors (last_name, first_name, email, department)
                VALUES (?, ?, ?, ?)
            ''', (last_name, first_name, email, department))
            conn.commit()
            return cursor.lastrowid

    def get_instructor_by_id(self, instructor_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM instructors WHERE instructor_id = ?', (instructor_id,))
            return cursor.fetchone()

    def update_instructor(self, instructor_id, **kwargs):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [instructor_id]
            cursor.execute(f'UPDATE instructors SET {fields} WHERE instructor_id = ?', values)
            conn.commit()

    def delete_instructor(self, instructor_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM instructors WHERE instructor_id = ?', (instructor_id,))
            conn.commit()
