import sqlite3
from typing import List, Tuple

DB_PATH = "attendance.db"

class AttendanceRepository:
    def fetch_attendance(self, course_code: str, section: str, room: str = None) -> List[Tuple[str, str, str]]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if room:
                cursor.execute("""
                    SELECT a.student_id, s.name, a.timestamp FROM attendance a
                    LEFT JOIN students s ON a.student_id = s.student_id
                    WHERE a.course_code = ? AND a.section = ? AND a.room = ?
                """, (course_code, section, room))
            else:
                cursor.execute("""
                    SELECT a.student_id, s.name, a.timestamp FROM attendance a
                    LEFT JOIN students s ON a.student_id = s.student_id
                    WHERE a.course_code = ? AND a.section = ?
                """, (course_code, section))
            return cursor.fetchall()

def get_attendance_repository():
    return AttendanceRepository()
