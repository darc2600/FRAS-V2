from fastapi import APIRouter, Query
import sqlite3
from typing import List, Dict
from services.db import get_connection

DB_PATH = "attendance.db"

router = APIRouter()

@router.get("/api/student-courses", tags=["Registration"])
def get_courses_for_student(student_id: str = Query(...)) -> List[Dict]:
    """
    Returns a list of courses and sections a student is enrolled in.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT course_code, section, room
            FROM student_courses
            WHERE student_id = ?
            """,
            (student_id,)
        )
        courses = cursor.fetchall()
    return [
        {"course_code": course_code, "section": section, "room": room}
        for course_code, section, room in courses
    ]
