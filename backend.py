import sqlite3
import os
import sys
print("UNIQUE BACKEND LOADED MARKER")
print(f"Current working directory: {os.getcwd()}")
# Ensure the application root is on sys.path so top-level imports (e.g. `models`) work
BASE_DIR = os.path.dirname(__file__)
if BASE_DIR and BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
    print(f"Inserted BASE_DIR to sys.path: {BASE_DIR}")
import asyncio
import sys

# Set event loop policy for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Depends, UploadFile, File, Form, Request, HTTPException
from typing import List, Dict
import secrets
import jwt
from datetime import datetime, timedelta
from datetime import timezone
from zoneinfo import ZoneInfo
from pydantic import BaseModel
from services.db import get_connection
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.cron import CronTrigger

JWT_SECRET = "dev-secret-change-me"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440
MANILA_TZ = ZoneInfo("Asia/Manila")

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

# Import admin permission function
from api.admin import require_admin_permission

# -----------------------
# Database setup
# -----------------------

import os

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

def init_db():
    with get_connection() as conn:
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

# Initialize database on startup
# init_db()

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
    allow_origins=["http://localhost:4200", "http://localhost:61146", "http://127.0.0.1:4200", "http://127.0.0.1:61146"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scheduler for marking absents
# scheduler = AsyncIOScheduler()

async def mark_daily_absents():
    """Mark absents for classes that have ended today."""
    print("[SCHEDULER] Running mark_daily_absents")
    now = datetime.now()
    current_day = now.strftime("%A")
    attendance_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    print(f"[SCHEDULER] Current day: {current_day}, date: {attendance_date}, time: {current_time}")

    with get_connection() as conn:
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
    """Mark absents for classes that have ended today."""
    print("[SCHEDULER] Running mark_daily_absents")
    now = datetime.now()
    current_day = now.strftime("%A")
    attendance_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    print(f"[SCHEDULER] Current day: {current_day}, date: {attendance_date}, time: {current_time}")

    with get_connection() as conn:
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
# @app.on_event("startup")
# async def startup_event():
#     from services.attendance_service import mark_automatic_absents
#     # Run automatic absent marking every 45 minutes during class hours (7 AM - 10 PM)
#     scheduler.add_job(mark_automatic_absents, CronTrigger(minute="*/45", hour="7-22"))
#     # Keep daily cleanup job at 11 PM
#     scheduler.add_job(mark_daily_absents, CronTrigger(hour=23, minute=0))
#     scheduler.start()
#     print("[SCHEDULER] Started automatic absent marking every 45 minutes (7 AM - 10 PM)")
#     print("[SCHEDULER] Started daily absent marking job at 11 PM")

# @app.on_event("shutdown")
# async def shutdown_event():
#     scheduler.shutdown()
#     print("[SCHEDULER] Stopped scheduler")# Tag metadata for grouping in Swagger UI
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

    with get_connection() as conn:
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
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT course_code, course_name FROM courses ORDER BY course_code")
        courses = cursor.fetchall()
        return [{"code": course[0], "name": course[1]} for course in courses]

@app.get("/api/courses/{course_code}/sections", tags=["Courses"])
async def get_sections_for_course(course_code: str):
    """Get all sections for a specific course across all rooms"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT c.section 
            FROM classes c
            JOIN courses co ON c.course_id = co.course_id
            WHERE co.course_code = ?
            ORDER BY c.section
        """, (course_code,))
        sections = cursor.fetchall()
        return [section[0] for section in sections]

@app.get("/api/rooms/{room_id}/courses/{course_code}/sections", tags=["Rooms"])
async def get_sections_for_course_and_room(room_id: int, course_code: str):
    """Get sections for a specific course in a specific room"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT c.section 
            FROM classes c
            JOIN courses co ON c.course_id = co.course_id
            WHERE co.course_code = ? AND c.room_id = ?
            ORDER BY c.section
        """, (course_code, room_id))
        sections = cursor.fetchall()
        return [section[0] for section in sections]

@app.get("/api/instructors", tags=["Instructors"])  
async def get_instructors():
    """Get all available instructors in 'Last, First' format"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_name, first_name FROM instructors ORDER BY last_name, first_name")
        instructors = cursor.fetchall()
        return [f"{inst[0]}, {inst[1]}" for inst in instructors]

# --- Student Validation Endpoint ---
@app.get("/api/students/{student_number}", tags=["Students"])
async def get_student_by_number(student_number: str):
    """Get student information by student number for validation"""
    with get_connection() as conn:
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

@app.get("/api/students", tags=["Students"])
async def get_all_students():
    """Get all students for dropdown selection"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, student_number, last_name, first_name, email FROM students ORDER BY last_name, first_name")
        students = cursor.fetchall()
        return [{
            "id": student[0],
            "student_number": student[1],
            "name": f"{student[2]}, {student[3]}",
            "email": student[4]
        } for student in students]

@app.get("/api/classes", tags=["Classes"])
async def get_all_classes():
    """Get all classes for dropdown selection"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.class_id, co.course_code, c.section, c.room_id, c.instructor_id,
                   i.first_name || ' ' || i.last_name as instructor_name
            FROM classes c
            LEFT JOIN courses co ON c.course_id = co.course_id
            LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
            ORDER BY co.course_code, c.section
        """)
        classes = cursor.fetchall()
        return [{
            "id": cls[0],
            "course_code": cls[1],
            "section": cls[2],
            "room_id": cls[3],
            "instructor_id": cls[4],
            "instructor_name": cls[5] or "Unknown"
        } for cls in classes]

# --- Debug Endpoint ---
@app.get("/test", tags=["Debug"])
async def test_endpoint():
    return "OK"

# Include additional routers
# try:
#     from api import auth
#     app.include_router(auth.router)
# except Exception as e:
#     print(f"Warning: could not include auth router: {e}")

# Include other API routers
# Temporarily disabled for debugging
for module_name in ['admin', 'auth', 'recognition', 'capture', 'registration', 'attendance', 'schedule']:
    try:
        module = __import__(f'api.{module_name}', fromlist=['router'])
        if hasattr(module, 'router'):
            app.include_router(module.router)
            print(f"✅ {module_name} router included")
    except Exception as e:
        print(f"Warning: could not include {module_name} router: {e}")

# Try direct imports
try:
    print("Attempting to import auth module...")
    from api import auth
    print("Auth module imported, including router...")
    app.include_router(auth.router)
    print("Auth router enabled")
    
    print("Attempting to import admin module...")
    from api import admin
    print("Admin module imported, including router...")
    app.include_router(admin.router)
    print("Admin router enabled")
    
    print("Attempting to import recognition module...")
    from api import recognition
    print("Recognition module imported, including router...")
    app.include_router(recognition.router)
    print("Recognition router enabled")
    
    print("All routers loaded successfully")
except Exception as e:
    print(f"Error loading routers: {e}")
    import traceback
    traceback.print_exc()

@app.post("/test-bulk")
async def update_system_settings_bulk():
    return {"message": "Test endpoint works"}

# Add support ticket endpoint
from pydantic import BaseModel
from typing import List, Optional

class SupportTicketCreate(BaseModel):
    subject: str
    description: str
    category: str = "other"
    priority: str = "medium"

@app.post("/api/support/tickets")
async def create_user_support_ticket(
    ticket: SupportTicketCreate,
    request: Request
):
    """Create a new support ticket (any authenticated user)"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(401, "Missing or invalid authorization header")

        token = auth_header.split(' ')[1]

        # Decode token manually
        import jwt
        JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
        JWT_ALGORITHM = "HS256"
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(400, "User ID not found in token")

        with get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now(timezone.utc).isoformat()

            db_url = (os.environ.get('DATABASE_URL') or '').strip().lower()
            is_postgres = bool(db_url) and not db_url.startswith('sqlite')

            if is_postgres:
                cursor.execute("""
                    INSERT INTO support_tickets (user_id, subject, description, category, priority, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    RETURNING ticket_id
                """, (user_id, ticket.subject, ticket.description, ticket.category, ticket.priority, now))
                row = cursor.fetchone()
                ticket_id = row[0] if row else None
            else:
                cursor.execute("""
                    INSERT INTO support_tickets (user_id, subject, description, category, priority, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, ticket.subject, ticket.description, ticket.category, ticket.priority, now))
                ticket_id = getattr(cursor, 'lastrowid', None)
                if not ticket_id:
                    cursor.execute("SELECT ticket_id FROM support_tickets WHERE user_id = ? ORDER BY ticket_id DESC LIMIT 1", (user_id,))
                    row = cursor.fetchone()
                    ticket_id = row[0] if row else None

            conn.commit()

            if ticket_id is None:
                raise HTTPException(500, "Failed to retrieve created ticket ID")

            return {"message": "Support ticket created successfully", "ticket_id": ticket_id}

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    except Exception as e:
        print(f"Error creating ticket: {str(e)}")
        raise HTTPException(500, f"Database error: {str(e)}")

# Add a simple test endpoint
# @app.get("/test")
# async def test_endpoint():
#     return {"message": "Server is running with CORS enabled!"}