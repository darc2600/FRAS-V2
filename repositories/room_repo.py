import sqlite3
from typing import List, Dict
from services.db import get_connection

DB_PATH = "attendance.db"

class RoomRepository:
    def fetch_rooms(self) -> List[str]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT room_number FROM rooms")
            return [row[0] for row in cursor.fetchall()]

    def fetch_courses(self, room: str) -> List[str]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT co.course_code FROM classes c JOIN courses co ON c.course_id = co.course_id JOIN rooms r ON c.room_id = r.room_id WHERE r.room_number = ?", (room,))
            return [row[0] for row in cursor.fetchall()]

    def fetch_sections(self, room: str, course: str) -> List[str]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT c.section FROM classes c JOIN courses co ON c.course_id = co.course_id JOIN rooms r ON c.room_id = r.room_id WHERE r.room_number = ? AND co.course_code = ?", (room, course))
            return [row[0] for row in cursor.fetchall()]

    def fetch_floor_levels(self) -> List[int]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT floor_level FROM rooms ORDER BY floor_level")
            return [row[0] for row in cursor.fetchall()]

    def fetch_rooms_by_floor(self, floor_level: int) -> List[Dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT room_id, room_number FROM rooms WHERE floor_level = ? ORDER BY room_number", (floor_level,))
            rows = cursor.fetchall()
            return [
                {"room_id": row[0], "room_number": row[1]}
                for row in rows
            ]

    def fetch_courses_sections_by_room(self, room_id: int) -> List[Dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT c.class_id, co.course_code, c.section
                FROM classes c
                JOIN courses co ON c.course_id = co.course_id
                WHERE c.room_id = ?
                ORDER BY co.course_code, c.section
            """, (room_id,))
            rows = cursor.fetchall()
            return [
                {"course_section": f"{row[1]}-{row[2]}", "course_code": row[1], "section": row[2], "class_id": row[0]}
                for row in rows
            ]

def get_room_repository():
    return RoomRepository()
