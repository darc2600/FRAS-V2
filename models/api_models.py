from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Student Models
class StudentBase(BaseModel):
    student_number: str = Field(..., min_length=1, max_length=20)
    last_name: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr

class StudentCreate(StudentBase):
    created_at: str

class StudentResponse(StudentBase):
    student_id: int
    face_data_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Course Models
class CourseResponse(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    units: Optional[int] = None
    dept_id: Optional[int] = None

# Instructor Models
class InstructorResponse(BaseModel):
    instructor_id: int
    instructor_number: str
    last_name: str
    first_name: str
    email: EmailStr
    dept_id: Optional[int] = None

# Attendance Models
class AttendanceLogResponse(BaseModel):
    student_number: str
    student_name: str
    timestamp: str
    status: str

class AttendanceRequest(BaseModel):
    course_code: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    room: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# Recognition Models
class RecognitionResponse(BaseModel):
    status: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    attendance_status: Optional[str] = None
    message: Optional[str] = None

# Registration Models
class ScheduleEntry(BaseModel):
    course_code: str
    section: str

class RegistrationRequest(BaseModel):
    student_number: str
    last_name: str
    first_name: str
    email: EmailStr
    created_at: str
    schedule: List[ScheduleEntry]

class RegistrationResponse(BaseModel):
    status: str
    message: str
    image_paths: List[str]

# Room Models
class RoomResponse(BaseModel):
    room_id: int
    room_number: str
    floor_level: int
    building_name: str
    room_type: str

class FloorResponse(BaseModel):
    floor_level: int
    room_count: int

# Schedule Models
class ClassSchedule(BaseModel):
    class_id: int
    course_code: str
    course_name: str
    section: str
    instructor_name: str
    day_of_week: str
    start_time: str
    end_time: str
    room_number: str

# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None