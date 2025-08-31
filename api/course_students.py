from fastapi import APIRouter, Query, Depends
import sqlite3
from typing import List, Dict

DB_PATH = "attendance.db"

router = APIRouter()

@router.get("/api/course-students", tags=["Registration"])
def get_students_in_course(
    course_code: str = Query(...),
    section: str = Query(...)
) -> List[Dict]:
    """
    Returns a list of students enrolled in the given course and section.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.student_id, s.name
            FROM students s
            JOIN student_courses sc ON s.student_id = sc.student_id
            WHERE sc.course_code = ? AND sc.section = ?
            """,
            (course_code, section)
        )
        students = cursor.fetchall()
    return [{"student_id": sid, "name": name} for sid, name in students]
