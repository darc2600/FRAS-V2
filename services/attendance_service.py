from repositories.attendance_repo import AttendanceRepository, get_attendance_repository
from models.attendance import AttendanceResponse
from fastapi import Depends
import sqlite3
import os
from datetime import datetime
from services.settings_service import get_settings_service
from repositories.recognition_repo import RecognitionRepository

class AttendanceService:
    def __init__(self, repo: AttendanceRepository):
        self.repo = repo

    def get_attendance(self, course_code: str, section: str, room: str = None, start_date: str = None, end_date: str = None) -> AttendanceResponse:
        records = self.repo.fetch_attendance(course_code, section, room, start_date, end_date)
        # Convert None values to appropriate defaults and ensure all fields are strings
        fixed_records = []
        for rec in records:
            student_id, student_name, timestamp, status = rec
            # Handle None values
            student_id = str(student_id) if student_id is not None else "Unknown"
            student_name = student_name if student_name is not None else "Unknown Student"
            timestamp = timestamp if timestamp is not None else ""
            status = status if status is not None else "Unknown"
            fixed_records.append((student_id, student_name, timestamp, status))
        return AttendanceResponse(attendance=fixed_records)

async def mark_automatic_absents():
    """Automatically mark absents for ongoing classes based on configurable threshold."""
    print("[SCHEDULER] Running mark_automatic_absents")

    settings = get_settings_service()
    auto_absent_threshold = settings.auto_mark_absent_after_minutes

    now = datetime.now()
    current_day = now.strftime("%A")
    attendance_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    print(f"[SCHEDULER] Current day: {current_day}, date: {attendance_date}, time: {current_time}")
    print(f"[SCHEDULER] Auto absent threshold: {auto_absent_threshold} minutes after class start")

    # Database path
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Get classes for today that have started and are past the auto-absent threshold
        cursor.execute('''
            SELECT class_id, start_time, end_time FROM classes
            WHERE day_of_week = ?
            AND start_time <= ?
            AND end_time > ?
        ''', (current_day, current_time, current_time))
        active_classes = cursor.fetchall()
        print(f"[SCHEDULER] Active classes today: {active_classes}")

        repo = RecognitionRepository()

        for class_id, start_time_str, end_time_str in active_classes:
            # Calculate if we're past the auto-absent threshold
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            current_time_obj = datetime.strptime(current_time, "%H:%M").time()

            # Create datetime objects for comparison
            today_start = datetime.combine(now.date(), start_time)
            today_current = datetime.combine(now.date(), current_time_obj)

            minutes_since_start = (today_current - today_start).total_seconds() / 60

            if minutes_since_start >= auto_absent_threshold:
                print(f"[SCHEDULER] Class {class_id} is {minutes_since_start:.1f} minutes past start, marking absents")
                await repo.mark_absents(class_id, attendance_date)
            else:
                print(f"[SCHEDULER] Class {class_id} is only {minutes_since_start:.1f} minutes past start, waiting")

    print("[SCHEDULER] mark_automatic_absents completed")

def get_attendance_service(repo: AttendanceRepository = Depends(get_attendance_repository)):
    return AttendanceService(repo)
