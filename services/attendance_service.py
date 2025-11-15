from repositories.attendance_repo import AttendanceRepository, get_attendance_repository
from models.attendance import AttendanceResponse
from fastapi import Depends

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

def get_attendance_service(repo: AttendanceRepository = Depends(get_attendance_repository)):
    return AttendanceService(repo)
