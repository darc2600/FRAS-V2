
from fastapi import APIRouter
import sqlite3
import os

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

@router.get("/api/rooms/floors")
def get_rooms_with_floors():
    print(f"[DEBUG] Using database file: {os.path.abspath(DB_PATH)}")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT room_id, floor_level, room_number FROM rooms")
        rows = cursor.fetchall()
        print(f"[DEBUG] /api/rooms/floors fetched rows: {rows}")
        rooms = [
            {"room_id": row[0], "floor_level": row[1], "room_number": row[2]}
            for row in rows
        ]
    return rooms
