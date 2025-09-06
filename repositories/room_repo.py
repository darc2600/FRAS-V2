import sqlite3
from typing import List

DB_PATH = "attendance.db"

class RoomRepository:
    def fetch_rooms(self) -> List[str]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT room_id FROM rooms")
            return [row[0] for row in cursor.fetchall()]

    def fetch_courses(self, room: str) -> List[str]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT course_code FROM classes WHERE room_id = ?", (room,))
            return [row[0] for row in cursor.fetchall()]

    def fetch_sections(self, room: str, course: str) -> List[str]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT section FROM classes WHERE room_id = ? AND course_code = ?", (room, course))
            return [row[0] for row in cursor.fetchall()]

def get_room_repository():
    return RoomRepository()
