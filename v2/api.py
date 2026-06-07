from datetime import date

from fastapi import APIRouter, Depends, Query

from v2.models import (
    V2CreateEventRequest,
    V2ManualAttendanceRequest,
    V2ProfessorScheduleResponse,
    V2ProfessorSummary,
    V2SessionDetailResponse,
    V2SessionReviewResponse,
    V2StartSessionRequest,
    V2TodayClassesResponse,
)
from v2.service import V2AttendanceService, get_v2_attendance_service


router = APIRouter(prefix="/api/v2", tags=["V2 Attendance"])


@router.get("/professors", response_model=list[V2ProfessorSummary])
def list_professors(
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.list_professors()


@router.get("/professors/{professor_id}/today/classes", response_model=V2TodayClassesResponse)
def get_today_classes(
    professor_id: int,
    target_date: date | None = Query(default=None),
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.get_today_classes(professor_id=professor_id, target_date=target_date)


@router.get("/professors/{professor_id}/schedule", response_model=V2ProfessorScheduleResponse)
def get_professor_schedule(
    professor_id: int,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.get_professor_schedule(professor_id=professor_id)


@router.post("/classes/{class_id}/sessions/start", response_model=V2SessionDetailResponse)
def start_session(
    class_id: int,
    payload: V2StartSessionRequest,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.start_session(class_id=class_id, payload=payload)


@router.get("/sessions/{session_id}", response_model=V2SessionDetailResponse)
def get_session(
    session_id: int,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.get_session_detail(session_id=session_id)


@router.post("/sessions/{session_id}/events", response_model=V2SessionDetailResponse)
def create_event(
    session_id: int,
    payload: V2CreateEventRequest,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.create_event(session_id=session_id, payload=payload)


@router.post("/sessions/{session_id}/manual-attendance", response_model=V2SessionDetailResponse)
def save_manual_attendance(
    session_id: int,
    payload: V2ManualAttendanceRequest,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.save_manual_attendance(session_id=session_id, payload=payload)


@router.post("/sessions/{session_id}/break/start", response_model=V2SessionDetailResponse)
def start_break(
    session_id: int,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.start_break(session_id=session_id)


@router.post("/sessions/{session_id}/break/end", response_model=V2SessionDetailResponse)
def end_break(
    session_id: int,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.end_break(session_id=session_id)


@router.post("/sessions/{session_id}/end", response_model=V2SessionReviewResponse)
def end_session(
    session_id: int,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.end_session(session_id=session_id)


@router.get("/sessions/{session_id}/review", response_model=V2SessionReviewResponse)
def get_session_review(
    session_id: int,
    service: V2AttendanceService = Depends(get_v2_attendance_service),
):
    return service.get_session_review(session_id=session_id)
