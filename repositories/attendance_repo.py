from services.db import get_connection
from typing import List, Tuple
import os


class AttendanceRepository:
    def fetch_attendance(self, course_code: str, section: str, room: str = None, start_date: str = None, end_date: str = None) -> List[Tuple[str, str, str]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            database_url = (os.environ.get('DATABASE_URL') or '').strip().lower()
            is_postgres = bool(database_url) and not database_url.startswith('sqlite')
            # Get course_id from course_code
            cursor.execute('SELECT course_id FROM courses WHERE course_code = ?', (course_code,))
            course_row = cursor.fetchone()
            if not course_row:
                return []
            course_id = course_row[0]
            # Lookup class_id from classes table
            if room:
                cursor.execute('''
                    SELECT class_id FROM classes
                    WHERE course_id = ? AND section = ? AND room_id = ?
                ''', (course_id, section, int(room)))
            else:
                cursor.execute('''
                    SELECT class_id FROM classes
                    WHERE course_id = ? AND section = ?
                ''', (course_id, section))
            class_row = cursor.fetchone()
            if not class_row:
                return []
            class_id = class_row[0]
            if start_date and end_date and start_date.strip() and end_date.strip():
                if is_postgres:
                    cursor.execute("""
                        SELECT s.student_number, (s.last_name || ', ' || s.first_name) AS student_name, a.timestamp, ast.status_name
                        FROM attendance_logs a
                        LEFT JOIN students s ON a.student_id = s.student_id
                        LEFT JOIN attendance_status_types ast ON a.status_id = ast.status_id
                        WHERE a.class_id = ?
                        AND ((a.timestamp AT TIME ZONE 'Asia/Manila')::date >= ?::date)
                        AND ((a.timestamp AT TIME ZONE 'Asia/Manila')::date <= ?::date)
                        ORDER BY a.timestamp
                    """, (class_id, start_date, end_date))
                else:
                    cursor.execute("""
                        SELECT s.student_number, (s.last_name || ', ' || s.first_name) AS student_name, a.timestamp, ast.status_name
                        FROM attendance_logs a
                        LEFT JOIN students s ON a.student_id = s.student_id
                        LEFT JOIN attendance_status_types ast ON a.status_id = ast.status_id
                        WHERE a.class_id = ?
                        AND DATE(datetime(a.timestamp, '+8 hours')) >= DATE(?)
                        AND DATE(datetime(a.timestamp, '+8 hours')) <= DATE(?)
                        ORDER BY a.timestamp
                    """, (class_id, start_date, end_date))
            else:
                cursor.execute("""
                    SELECT s.student_number, (s.last_name || ', ' || s.first_name) AS student_name, a.timestamp, ast.status_name 
                    FROM attendance_logs a
                    LEFT JOIN students s ON a.student_id = s.student_id
                    LEFT JOIN attendance_status_types ast ON a.status_id = ast.status_id
                    WHERE a.class_id = ?
                    ORDER BY a.timestamp
                """, (class_id,))
            return cursor.fetchall()


def get_attendance_repository():
    return AttendanceRepository()
