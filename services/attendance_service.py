from repositories.attendance_repo import AttendanceRepository, get_attendance_repository
from models.attendance import AttendanceResponse
from fastapi import Depends

class AttendanceService:
    def __init__(self, repo: AttendanceRepository):
        self.repo = repo

    def get_attendance(self, course_code: str, section: str, room: str = None) -> AttendanceResponse:
        records = self.repo.fetch_attendance(course_code, section, room)
        return AttendanceResponse(attendance=records)

def get_attendance_service(repo: AttendanceRepository = Depends(get_attendance_repository)):
    return AttendanceService(repo)
