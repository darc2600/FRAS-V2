from services.db import get_connection


def _is_postgres_backend():
    import os
    db_url = (os.environ.get("DATABASE_URL") or "").strip().lower()
    return bool(db_url) and not db_url.startswith("sqlite")


class AttendanceLogRepository:
    def add_log(self, student_id, class_id, status):
        with get_connection() as conn:
            cursor = conn.cursor()
            # Get status_id from attendance_status_types table
            cursor.execute('''
                SELECT status_id FROM attendance_status_types WHERE status_name = ?
            ''', (status,))
            status_row = cursor.fetchone()
            if not status_row:
                raise ValueError(f"Invalid status: {status}")
            status_id = status_row[0]
            
            # Create descriptive note
            from datetime import datetime
            note = f"Manually recorded as {status} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            if _is_postgres_backend():
                cursor.execute('''
                    INSERT INTO attendance_logs (student_id, class_id, status_id, notes)
                    VALUES (?, ?, ?, ?)
                    RETURNING log_id
                ''', (student_id, class_id, status_id, note))
                row = cursor.fetchone()
                conn.commit()
                return row[0] if row else None

            cursor.execute('''
                INSERT INTO attendance_logs (student_id, class_id, status_id, notes)
                VALUES (?, ?, ?, ?)
            ''', (student_id, class_id, status_id, note))
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
