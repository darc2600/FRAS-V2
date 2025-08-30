import sqlite3
from typing import List, Tuple

DB_PATH = "attendance.db"

class AttendanceRepository:
    def fetch_attendance(self, course_code: str, section: str, room: str = None) -> List[Tuple[str, str]]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if room:
                cursor.execute("""
                    SELECT student_id, timestamp FROM attendance
                    WHERE course_code = ? AND section = ? AND room = ?
                """, (course_code, section, room))
            else:
                cursor.execute("""
                    SELECT student_id, timestamp FROM attendance
                    WHERE course_code = ? AND section = ?
                """, (course_code, section))
            return cursor.fetchall()

def get_attendance_repository():
    return AttendanceRepository()
