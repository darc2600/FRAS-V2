from services.db import get_connection


class AttendanceLogRepository:
    def add_log(self, student_id, class_id, status):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO attendance_logs (student_id, class_id, status)
                VALUES (?, ?, ?)
            ''', (student_id, class_id, status))
            conn.commit()
            try:
                return cursor.lastrowid
            except Exception:
                return None

    def get_logs_by_student(self, student_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM attendance_logs WHERE student_id = ?', (student_id,))
            return cursor.fetchall()

    def get_logs_by_class(self, class_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM attendance_logs WHERE class_id = ?', (class_id,))
            return cursor.fetchall()

    def update_log(self, log_id, **kwargs):
        with get_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join([f"{k}=?" for k in kwargs])
            values = list(kwargs.values()) + [log_id]
            cursor.execute(f'UPDATE attendance_logs SET {fields} WHERE log_id = ?', values)
            conn.commit()

    def delete_log(self, log_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attendance_logs WHERE log_id = ?', (log_id,))
            conn.commit()
