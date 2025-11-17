import sqlite3
import os
import sys
print("UNIQUE BACKEND LOADED MARKER")
print(f"Current working directory: {os.getcwd()}")
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request
from typing import List
import secrets
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

JWT_SECRET = "dev-secret-change-me"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440

# Optional imports for secure password hashing / verification
try:
	from passlib.hash import pbkdf2_sha256, bcrypt
	_HAS_PASSLIB = True
except ImportError:
	pbkdf2_sha256 = None
	bcrypt = None
	_HAS_PASSLIB = False

class UserRegister(BaseModel):
    email: str
    password: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# -----------------------
# Database setup
# -----------------------

import os

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

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
                email TEXT UNIQUE,
                password TEXT,
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

        # ATTENDANCE_STATUS_TYPES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_status_types (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_code VARCHAR(20) UNIQUE NOT NULL,
                status_name VARCHAR(50) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
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
                status_id INTEGER,
                notes TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(class_id) REFERENCES classes(class_id),
                FOREIGN KEY(status_id) REFERENCES attendance_status_types(status_id)
            )
        ''')

        # ADMINS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_number TEXT UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT,
                dept_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
            )
        ''')

        # USERS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT,
                reference_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Triggers to auto-update updated_at on row update
        for table in [
            'students', 'instructors', 'courses', 'departments', 'room_types', 'attendance_status_types', 'campuses', 'buildings', 'rooms', 'school_terms', 'classes', 'enrollments', 'attendance_logs', 'admins', 'users'
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
from services.attendance_service import get_attendance_service


# Use the real RecognitionService from services/recognition_service.py
# # from services.recognition_service import get_recognition_service


# Use the real RegistrationService from services/registration_service.py
from services.registration_service import get_registration_service

# Use the real RoomService from services/room_service.py
from services.room_service import get_room_service

class CaptureService:
    async def capture_image(self, file, course_code, section, student_id):
        return {"captured": True, "student_id": student_id}
def get_capture_service():
    return CaptureService()


from services.schedule_service import get_schedule_service

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

# Scheduler for marking absents
scheduler = AsyncIOScheduler()

async def mark_daily_absents():
    """Mark absents for classes that have ended today."""
    print("[SCHEDULER] Running mark_daily_absents")
    now = datetime.now()
    current_day = now.strftime("%A")
    attendance_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    print(f"[SCHEDULER] Current day: {current_day}, date: {attendance_date}, time: {current_time}")
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Get classes for today that have ended
        cursor.execute('''
            SELECT class_id, end_time FROM classes 
            WHERE day_of_week = ? AND end_time < ?
        ''', (current_day, current_time))
        ended_classes = cursor.fetchall()
        print(f"[SCHEDULER] Ended classes: {ended_classes}")
        
        for class_id, end_time_str in ended_classes:
            # Mark absents for this class and date
            from repositories.recognition_repo import RecognitionRepository
            repo = RecognitionRepository()
            result = await repo.mark_absents(class_id, attendance_date)
            print(f"[SCHEDULER] Marked absents for class {class_id} on {attendance_date}: {result}")

# Start scheduler on startup
@app.on_event("startup")
async def startup_event():
    scheduler.add_job(mark_daily_absents, CronTrigger(hour=23, minute=0))  # Daily at 11 PM
    scheduler.start()
    print("[SCHEDULER] Started daily absent marking job at 11 PM")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("[SCHEDULER] Stopped scheduler")

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

# --- User Registration Endpoint ---
@app.post("/api/user/register", response_model=None, tags=["User"])
async def register_user(payload: UserRegister):
    print("Registration endpoint called")
    print(f"Current dir: {os.getcwd()}")
    print(f"DB_PATH: {DB_PATH}")
    print(f"Registering user: {payload.email}")
    print(f"_HAS_PASSLIB: {_HAS_PASSLIB}")
    # Hash the password
    if _HAS_PASSLIB:
        if pbkdf2_sha256 is not None:
            stored = pbkdf2_sha256.hash(payload.password)
        elif bcrypt is not None:
            stored = bcrypt.hash(payload.password)
        else:
            stored = payload.password
    else:
        stored = payload.password  # fallback

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        
        # Add columns if they don't exist (for existing tables)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN reference_id INTEGER")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        
        # Check if user already exists in users table
        cur.execute("SELECT user_id FROM users WHERE email = ?", (payload.email,))
        existing_user = cur.fetchone()
        if existing_user:
            return {"error": "User already registered. Please login instead."}
        
        # Determine role and reference_id
        role = None
        reference_id = None
        
        # Check if email exists in instructors table
        cur.execute("SELECT instructor_id FROM instructors WHERE email = ?", (payload.email,))
        instructor_result = cur.fetchone()
        if instructor_result:
            role = "instructor"
            reference_id = instructor_result[0]
        
        # Check if email exists in admins table
        cur.execute("SELECT admin_id FROM admins WHERE email = ?", (payload.email,))
        admin_result = cur.fetchone()
        if admin_result:
            role = "admin"
            reference_id = admin_result[0]
        
        if not role:
            return {"error": "Email not found in system. Please contact administrator."}
        
        # Create user record
        try:
            cur.execute("""
                INSERT INTO users (email, password, role, reference_id) 
                VALUES (?, ?, ?, ?)
            """, (payload.email, stored, role, reference_id))
            
            # Get the user_id of the inserted record
            cur.execute("SELECT user_id FROM users WHERE email = ?", (payload.email,))
            user_id = cur.fetchone()[0]
            conn.commit()
        except Exception as e:
            conn.rollback()
            return {"error": f"Database error: {str(e)}"}
        
        # Create JWT token
        access_token = create_access_token(data={"sub": payload.email, "role": role, "user_id": user_id})
        
        print(f"Registration successful: user_id={user_id}, role={role}, reference_id={reference_id}")
        print(f"User registered with email: {payload.email}")
        return {"access_token": access_token, "token_type": "bearer", "role": role, "user_id": user_id}

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
)# --- Capture Endpoint ---
@app.post("/api/capture", response_model=None, tags=["Capture"])
async def capture_image(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...), student_id: str = Form(...), capture_service=Depends(get_capture_service)):
    return await capture_service.capture_image(file, course_code, section, student_id)

# --- Schedule Endpoints ---
@app.get("/api/room-schedule/{room_id}", response_model=None, tags=["Schedule"])
async def get_room_schedule(room_id: str, schedule_service=Depends(get_schedule_service)):
    return await schedule_service.get_room_schedule(room_id)

@app.post("/api/room-schedule/{room_id}", response_model=None, tags=["Schedule"])
async def update_room_schedule(room_id: str, request: Request, schedule_service=Depends(get_schedule_service)):
    return await schedule_service.update_room_schedule(room_id, request)

@app.delete("/api/room-schedule/{room_id}", tags=["Schedule"])
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

# --- Student Validation Endpoint ---
@app.get("/api/students/{student_number}", tags=["Students"])
async def get_student_by_number(student_number: str):
    """Get student information by student number for validation"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, student_number, last_name, first_name, email FROM students WHERE student_number = ?", (student_number,))
        student = cursor.fetchone()
        if student:
            return {
                "student_id": student[0],
                "student_number": student[1],
                "last_name": student[2],
                "first_name": student[3],
                "email": student[4]
            }
        else:
            return None

# --- Debug Endpoint ---
@app.get("/api/routes", tags=["Debug"])
async def list_routes():
    return [route.path for route in app.routes]

# Include additional routers
try:
    from api import auth
    app.include_router(auth.router)
except Exception as e:
    print(f"Warning: could not include auth router: {e}")

try:
    from api import professors
    app.include_router(professors.router)
except Exception as e:
    print(f"Warning: could not include professors router: {e}")

# Include other API routers
for module_name in ['attendance', 'auth', 'capture', 'course_students', 'debug', 'recognition', 'registration', 'schedule', 'student_courses']:
    try:
        module = __import__(f'api.{module_name}', fromlist=['router'])
        if hasattr(module, 'router'):
            app.include_router(module.router)
    except Exception as e:
        print(f"Warning: could not include {module_name} router: {e}")
