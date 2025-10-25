import sqlite3
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request
from typing import List

# -----------------------
# Database setup
# -----------------------

DB_PATH = "attendance.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # STUDENTS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number VARCHAR(20) UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT,
                face_data_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # INSTRUCTORS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instructors (
                instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instructor_number VARCHAR(20) UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT,
                dept_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
            )
        ''')

        # COURSES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code VARCHAR(20) UNIQUE,
                course_name VARCHAR(100),
                units INTEGER,
                dept_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
            )
        ''')

        # DEPARTMENTS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_code VARCHAR(20) UNIQUE,
                dept_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ROOM_TYPES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_types (
                room_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name VARCHAR(50) UNIQUE
            )
        ''')

        # CAMPUSES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campuses (
                campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                campus_name TEXT UNIQUE NOT NULL,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # BUILDINGS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS buildings (
                building_id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_name TEXT NOT NULL,
                campus_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(campus_id) REFERENCES campuses(campus_id),
                UNIQUE(building_name, campus_id)
            )
        ''')

        # ROOMS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number VARCHAR(20),
                floor_level INTEGER,
                campus_id INTEGER NOT NULL,
                building_id INTEGER,
                room_type_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(campus_id) REFERENCES campuses(campus_id),
                FOREIGN KEY(building_id) REFERENCES buildings(building_id),
                FOREIGN KEY(room_type_id) REFERENCES room_types(room_type_id)
            )
        ''')

        # SCHOOL_TERMS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_terms (
                term_id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_year VARCHAR(20),
                term INTEGER,
                start_date DATE,
                end_date DATE
            )
        ''')

        # CLASSES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                room_id INTEGER,
                instructor_id INTEGER,
                section VARCHAR(10),
                day_of_week VARCHAR(10),
                start_time TIME,
                end_time TIME,
                term_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(course_id) REFERENCES courses(course_id),
                FOREIGN KEY(room_id) REFERENCES rooms(room_id),
                FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id),
                FOREIGN KEY(term_id) REFERENCES school_terms(term_id)
            )
        ''')

        # ENROLLMENTS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                class_id INTEGER,
                enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(class_id) REFERENCES classes(class_id)
            )
        ''')

        # ATTENDANCE_LOGS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                class_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(class_id) REFERENCES classes(class_id)
            )
        ''')

        # Triggers to auto-update updated_at on row update
        for table in [
            'students', 'instructors', 'courses', 'departments', 'room_types', 'campuses', 'buildings', 'rooms', 'school_terms', 'classes', 'enrollments', 'attendance_logs'
        ]:
            cursor.execute(f'''
                CREATE TRIGGER IF NOT EXISTS trg_{table}_updated_at
                AFTER UPDATE ON {table}
                FOR EACH ROW
                BEGIN
                    UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid;
                END;
            ''')

        conn.commit()

# Initialize DB on startup
init_db()

# -----------------------
# FastAPI app setup
# -----------------------


# -----------------------
# Service Classes & Dependency Providers
# -----------------------

# Dummy response models for FastAPI (replace with your actual Pydantic models if available)
class AttendanceResponse(dict): pass
class RecognitionResponse(dict): pass
class RegistrationResponse(dict): pass
class CaptureResponse(dict): pass
class ScheduleResponse(dict): pass


# Use the real AttendanceService from services/attendance_service.py
from services.attendance_service import AttendanceService, get_attendance_service


# Use the real RecognitionService from services/recognition_service.py
from services.recognition_service import RecognitionService, get_recognition_service


# Use the real RegistrationService from services/registration_service.py
from services.registration_service import RegistrationService, get_registration_service

# Use the real RoomService from services/room_service.py
from services.room_service import RoomService, get_room_service

class CaptureService:
    async def capture_image(self, file, course_code, section, student_id):
        return {"captured": True, "student_id": student_id}
def get_capture_service():
    return CaptureService()


from services.schedule_service import ScheduleService, get_schedule_service

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tag metadata for grouping in Swagger UI
tags_metadata = [
    {"name": "Rooms", "description": "Room listing and related endpoints."},
    {"name": "Courses", "description": "Course listing and related endpoints."},
    {"name": "Sections", "description": "Section listing and related endpoints."},
    {"name": "Attendance", "description": "Attendance retrieval and management."},
    {"name": "Registration", "description": "Student registration and management."},
    {"name": "Recognition", "description": "Face recognition endpoints."},
    {"name": "Capture", "description": "Image capture endpoints."},
    {"name": "Debug", "description": "Debug and utility endpoints."},
]
app.openapi_tags = tags_metadata

# -----------------------
# API Endpoints
# -----------------------

@app.get("/api/rooms", tags=["Rooms"])
async def get_rooms(room_service=Depends(get_room_service)):
    return room_service.get_rooms()

@app.get("/api/rooms/{room_id}/courses", tags=["Rooms"])
async def get_courses(room_id: str, room_service=Depends(get_room_service)):
    return room_service.get_courses(room_id)

@app.get("/api/rooms/{room_id}/courses/{course_code}/sections", tags=["Rooms"])
async def get_sections(room_id: str, course_code: str, room_service=Depends(get_room_service)):
    return room_service.get_sections(room_id, course_code)

# --- Floor and Room Selection Endpoints ---
@app.get("/api/floors", tags=["Rooms"])
async def get_floor_levels(room_service=Depends(get_room_service)):
    """Get all unique floor levels"""
    return room_service.get_floor_levels()

@app.get("/api/floors/{floor_level}/rooms", tags=["Rooms"])
async def get_rooms_by_floor(floor_level: int, room_service=Depends(get_room_service)):
    """Get all rooms on a specific floor level"""
    return room_service.get_rooms_by_floor(floor_level)

@app.get("/api/rooms/{room_id}/courses-sections", tags=["Rooms"])
async def get_courses_sections_by_room(room_id: int, room_service=Depends(get_room_service)):
    """Get all courses and sections for a specific room"""
    return room_service.get_courses_sections_by_room(room_id)

# --- Attendance Endpoint ---
@app.get("/api/attendance", response_model=None, tags=["Attendance"])
async def get_attendance(course_code: str, section: str, room: str = None, start_date: str = None, end_date: str = None, attendance_service=Depends(get_attendance_service)):
    return attendance_service.get_attendance(course_code, section, room, start_date, end_date)

# --- Recognition Endpoint ---
@app.post("/api/recognize", response_model=None, tags=["Recognition"])
async def recognize_face(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...), room: str = Form(...), recognition_service=Depends(get_recognition_service)):
    return await recognition_service.recognize_face(file, course_code, section, room)

# --- Registration Endpoint ---
@app.post("/api/register", response_model=None, tags=["Registration"])
async def register_student(
    student_number: str = Form(...),
    last_name: str = Form(...),
    first_name: str = Form(...),
    email: str = Form(...),
    created_at: str = Form(...),
    schedule: str = Form(...),
    images: List[UploadFile] = File(...),
    registration_service=Depends(get_registration_service)
):
    return await registration_service.register_student(
        student_number, last_name, first_name, email, created_at, schedule, images
    )

# --- Capture Endpoint ---
@app.post("/api/capture", response_model=None, tags=["Capture"])
async def capture_image(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...), student_id: str = Form(...), capture_service=Depends(get_capture_service)):
    return await capture_service.capture_image(file, course_code, section, student_id)

# --- Schedule Endpoints ---
@app.get("/api/schedule/{room_id}", response_model=None, tags=["Schedule"])
async def get_room_schedule(room_id: str, schedule_service=Depends(get_schedule_service)):
    return await schedule_service.get_room_schedule(room_id)

@app.post("/api/schedule/{room_id}", response_model=None, tags=["Schedule"])
async def update_room_schedule(room_id: str, request: Request, schedule_service=Depends(get_schedule_service)):
    return await schedule_service.update_room_schedule(room_id, request)

@app.delete("/api/schedule/{room_id}", tags=["Schedule"])
async def delete_room_schedule(room_id: str, schedule_service=Depends(get_schedule_service)):
    return await schedule_service.delete_room_schedule(room_id)

# --- Course and Instructor Data Endpoints ---
@app.get("/api/courses", tags=["Courses"])
async def get_courses():
    """Get all available course codes"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT course_code, course_name FROM courses ORDER BY course_code")
        courses = cursor.fetchall()
        return [{"code": course[0], "name": course[1]} for course in courses]

@app.get("/api/instructors", tags=["Instructors"])  
async def get_instructors():
    """Get all available instructors in 'Last, First' format"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_name, first_name FROM instructors ORDER BY last_name, first_name")
        instructors = cursor.fetchall()
        return [f"{inst[0]}, {inst[1]}" for inst in instructors]

# --- Debug Endpoint ---
@app.get("/api/routes", tags=["Debug"])
async def list_routes():
    return [route.path for route in app.routes]
