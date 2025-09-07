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
                last_name TEXT,
                first_name TEXT,
                email TEXT,
                department TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # COURSES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_code VARCHAR(20) PRIMARY KEY,
                course_name VARCHAR(100),
                units INTEGER,
                department TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ROOMS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id VARCHAR(20) PRIMARY KEY,
                floor_level INTEGER,
                room_number VARCHAR(10),
                building_name VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # CLASSES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                class_id VARCHAR(20) PRIMARY KEY,
                course_code VARCHAR(20),
                room_id VARCHAR(20),
                instructor_id INTEGER,
                section VARCHAR(10),
                day_of_week VARCHAR(10),
                start_time TIME,
                end_time TIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(course_code) REFERENCES courses(course_code),
                FOREIGN KEY(room_id) REFERENCES rooms(room_id),
                FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id)
            )
        ''')

        # ENROLLMENTS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                class_id VARCHAR(20),
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
                class_id VARCHAR(20),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(class_id) REFERENCES classes(class_id)
            )
        ''')

        # Triggers to auto-update updated_at on row update
        for table in [
            'students', 'instructors', 'courses', 'rooms', 'classes', 'enrollments', 'attendance_logs'
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

class RoomService:
    def get_rooms(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rooms")
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
    def get_courses(self, room_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM classes WHERE room_id = ?", (room_id,))
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
    def get_sections(self, room_id, course_code):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM classes WHERE room_id = ? AND course_code = ?", (room_id, course_code))
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

def get_room_service():
    return RoomService()

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

# --- Attendance Endpoint ---
@app.get("/api/attendance", response_model=None, tags=["Attendance"])
async def get_attendance(course_code: str, section: str, room: str = None, attendance_service=Depends(get_attendance_service)):
    return attendance_service.get_attendance(course_code, section, room)

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

# --- Debug Endpoint ---
@app.get("/api/routes", tags=["Debug"])
async def list_routes():
    return [route.path for route in app.routes]
