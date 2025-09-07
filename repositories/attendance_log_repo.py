import sqlite3

DB_PATH = "attendance.db"

class AttendanceLogRepository:
    def add_log(self, student_id, class_id, status):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO attendance_logs (student_id, class_id, status)
                VALUES (?, ?, ?)
            ''', (student_id, class_id, status))
            conn.commit()
            return cursor.lastrowid

    def get_logs_by_student(self, student_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM attendance_logs WHERE student_id = ?', (student_id,))
            return cursor.fetchall()

    def get_logs_by_class(self, class_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM attendance_logs WHERE class_id = ?', (class_id,))
            return cursor.fetchall()

    def update_log(self, log_id, **kwargs):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [log_id]
            cursor.execute(f'UPDATE attendance_logs SET {fields} WHERE log_id = ?', values)
            conn.commit()

    def delete_log(self, log_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attendance_logs WHERE log_id = ?', (log_id,))
            conn.commit()
