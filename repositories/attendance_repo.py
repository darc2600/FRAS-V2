import sqlite3
from typing import List, Tuple

DB_PATH = "attendance.db"

class AttendanceRepository:
    def fetch_attendance(self, course_code: str, section: str, room: str = None) -> List[Tuple[str, str, str]]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Lookup class_id from classes table
            if room:
                cursor.execute('''
                    SELECT class_id FROM classes
                    WHERE course_code = ? AND section = ? AND room_id = ?
                ''', (course_code, section, room))
            else:
                cursor.execute('''
                    SELECT class_id FROM classes
                    WHERE course_code = ? AND section = ?
                ''', (course_code, section))
            class_row = cursor.fetchone()
            if not class_row:
                return []
            class_id = class_row[0]
            cursor.execute("""
                SELECT a.student_id, (s.last_name || ', ' || s.first_name) AS student_name, a.timestamp FROM AttendanceLogs a
                LEFT JOIN students s ON a.student_id = s.student_id
                WHERE a.class_id = ?
            """, (class_id,))
            return cursor.fetchall()

def get_attendance_repository():
    return AttendanceRepository()
