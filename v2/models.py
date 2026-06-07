from datetime import date, datetime, time
from typing import Literal, Optional

from pydantic import BaseModel, Field


class V2ClassCard(BaseModel):
    class_id: int
    course_code: str
    course_name: str
    section: str
    room: str
    day_of_week: str
    start_time: time
    end_time: time
    student_count: int
    status: Literal["current", "upcoming", "completed"]
    active_session_id: Optional[int] = None


class V2ProfessorScheduleClass(BaseModel):
    class_id: int
    course_code: str
    course_name: str
    section: str
    room: str
    day_of_week: str
    start_time: time
    end_time: time
    student_count: int


class V2TodayClassesResponse(BaseModel):
    professor_id: int
    date: date
    current: list[V2ClassCard]
    upcoming: list[V2ClassCard]
    completed: list[V2ClassCard]


class V2ProfessorScheduleResponse(BaseModel):
    professor_id: int
    classes: list[V2ProfessorScheduleClass]


class V2ProfessorSummary(BaseModel):
    professor_id: int
    user_id: Optional[int] = None
    faculty_number: Optional[str] = None
    professor_name: str
    email: str
    total_units: int = 0
    lecture_units: int = 0
    lab_units: int = 0


class V2StartSessionRequest(BaseModel):
    professor_id: int = 1
    session_date: Optional[date] = None


class V2SessionResponse(BaseModel):
    session_id: int
    class_id: int
    professor_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    session_status: str
    student_record_count: int


class V2StudentRecord(BaseModel):
    record_id: int
    student_id: int
    student_number: str
    student_name: str
    final_status: str
    system_assessment: str
    time_in: Optional[datetime] = None
    time_out: Optional[datetime] = None
    total_presence_minutes: int
    total_outside_minutes: int
    break_count: int
    late_minutes: int
    requires_review: bool
    review_reason: Optional[str] = None


class V2AttendanceEvent(BaseModel):
    event_id: int
    session_id: int
    record_id: Optional[int] = None
    student_id: Optional[int] = None
    event_type: str
    event_time: datetime
    event_source: str
    recognition_confidence: Optional[float] = None
    notes: Optional[str] = None
    is_voided: bool


class V2SessionDetailResponse(BaseModel):
    session: V2SessionResponse
    roster: list[V2StudentRecord]
    events: list[V2AttendanceEvent]


class V2CreateEventRequest(BaseModel):
    student_id: int
    event_type: Literal[
        "time_in",
        "break_out",
        "break_in",
        "time_out",
        "manual_attendance",
        "manual_capture",
        "false_recognition",
        "missed_recognition",
        "camera_failure",
        "network_failure",
    ]
    event_source: Literal["facial_recognition", "manual_professor", "system"] = "manual_professor"
    event_time: Optional[datetime] = None
    recognition_confidence: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None


class V2ManualAttendanceRecord(BaseModel):
    record_id: int
    student_id: int
    status: Literal["present", "absent", "late", "excused"]


class V2ManualAttendanceRequest(BaseModel):
    professor_id: int = 1
    records: list[V2ManualAttendanceRecord]
    notes: Optional[str] = None


class V2ReviewSummary(BaseModel):
    present_count: int
    late_count: int
    partial_count: int
    absent_count: int
    excused_count: int
    students_requiring_review: int
    total_students: int
    presence_validation_rate: float


class V2SessionReviewResponse(BaseModel):
    session: V2SessionResponse
    summary: V2ReviewSummary
    roster: list[V2StudentRecord]


class V2SessionHistoryClassContext(BaseModel):
    class_id: int
    course_code: str
    course_name: str
    section: str
    room: str
    professor_name: str


class V2SessionHistoryRow(BaseModel):
    session_id: int
    date: date
    scheduled_start: datetime
    scheduled_end: datetime
    attendance_count: int
    total_students: int
    attendance_rate: float
    average_presence_minutes: int
    warning_count: int
    excused_count: int
    status: Literal["completed", "needs_review", "in_progress"]


class V2SessionHistorySummary(BaseModel):
    total_sessions: int
    average_attendance_rate: float
    average_presence_minutes: int
    sessions_requiring_review: int
    excused_students: int


class V2SessionHistoryResponse(BaseModel):
    class_context: Optional[V2SessionHistoryClassContext] = None
    summary: V2SessionHistorySummary
    sessions: list[V2SessionHistoryRow]


class V2ClassRosterContext(BaseModel):
    class_id: int
    course_code: str
    course_name: str
    section: str
    room: str
    professor_name: str
    student_count: int


class V2ClassRosterHistoryItem(BaseModel):
    session_id: int
    session_date: date
    status: str
    note: str


class V2ClassRosterStudent(BaseModel):
    student_id: int
    student_number: str
    student_name: str
    email: Optional[str] = None
    face_profile_status: Literal["registered", "needs_update", "no_face_profile"]
    recognition_status: Literal["active", "low_confidence", "not_recognized_recently", "not_available"]
    attendance_rate: float
    last_face_update: Optional[datetime] = None
    recognition_confidence: Optional[float] = None
    total_sessions: int
    present_sessions: int
    late_sessions: int
    partial_sessions: int
    absent_sessions: int
    excused_sessions: int
    recent_history: list[V2ClassRosterHistoryItem]


class V2ClassRosterResponse(BaseModel):
    class_context: V2ClassRosterContext
    students: list[V2ClassRosterStudent]


class V2StudentClassHistoryHeader(BaseModel):
    class_id: int
    student_id: int
    student_name: str
    student_number: str
    course_code: str
    course_name: str
    section: str
    room: str
    attendance_rate: float


class V2StudentClassHistorySummary(BaseModel):
    total_sessions: int
    present_sessions: int
    late_sessions: int
    partial_sessions: int
    absent_sessions: int
    excused_sessions: int
    attendance_rate: float


class V2StudentClassHistoryRow(BaseModel):
    session_id: int
    session_date: date
    scheduled_start: datetime
    scheduled_end: datetime
    attendance_status: str
    presence_duration_minutes: int
    outside_duration_minutes: int
    break_count: int
    system_assessment: str


class V2StudentClassHistoryResponse(BaseModel):
    header: V2StudentClassHistoryHeader
    summary: V2StudentClassHistorySummary
    records: list[V2StudentClassHistoryRow]


class V2FaceProfileContextResponse(BaseModel):
    class_id: int
    student_id: int
    student_name: str
    student_number: str
    course_code: str
    course_name: str
    section: str
    room: str
    face_profile_status: Literal["registered", "needs_update", "no_face_profile"]
    last_face_update: Optional[datetime] = None


class V2FaceProfileSaveResponse(BaseModel):
    status: str
    message: str
    student_id: int
    face_profile_status: Literal["registered", "needs_update", "no_face_profile"]
    saved_angles: list[str]
    image_paths: list[str]


class V2RecognitionMatchResponse(BaseModel):
    status: Literal["success", "failed", "error"]
    message: Optional[str] = None
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=100)
