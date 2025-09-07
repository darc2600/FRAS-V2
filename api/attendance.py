from fastapi import APIRouter, Depends, Query
from services.attendance_service import AttendanceService, get_attendance_service
from models.attendance import AttendanceResponse

router = APIRouter()

@router.get("/api/attendance", response_model=AttendanceResponse)
def get_attendance(
    course_code: str = Query(...),
    section: str = Query(...),
    room: str = Query(None),
    service: AttendanceService = Depends(get_attendance_service)
):
    return service.get_attendance(course_code, section, room)
