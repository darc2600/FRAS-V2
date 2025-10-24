import sqlite3
from typing import List

DB_PATH = "attendance.db"

class RoomRepository:
    def fetch_rooms(self) -> List[str]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT room_number FROM rooms")
            return [row[0] for row in cursor.fetchall()]

    def fetch_courses(self, room: str) -> List[str]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT co.course_code FROM classes c JOIN courses co ON c.course_id = co.course_id JOIN rooms r ON c.room_id = r.room_id WHERE r.room_number = ?", (room,))
            return [row[0] for row in cursor.fetchall()]

    def fetch_sections(self, room: str, course: str) -> List[str]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT c.section FROM classes c JOIN courses co ON c.course_id = co.course_id JOIN rooms r ON c.room_id = r.room_id WHERE r.room_number = ? AND co.course_code = ?", (room, course))
            return [row[0] for row in cursor.fetchall()]

def get_room_repository():
    return RoomRepository()
