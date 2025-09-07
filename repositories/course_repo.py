import sqlite3

DB_PATH = "attendance.db"

class CourseRepository:
    def add_course(self, course_code, course_name, units, department):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO courses (course_code, course_name, units, department)
                VALUES (?, ?, ?, ?)
            ''', (course_code, course_name, units, department))
            conn.commit()
            return course_code

    def get_course(self, course_code):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM courses WHERE course_code = ?', (course_code,))
            return cursor.fetchone()

    def update_course(self, course_code, **kwargs):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [course_code]
            cursor.execute(f'UPDATE courses SET {fields} WHERE course_code = ?', values)
            conn.commit()

    def delete_course(self, course_code):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM courses WHERE course_code = ?', (course_code,))
            conn.commit()
