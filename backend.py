
# -----------------------
print("[DEBUG] backend.py loaded (test for correct file)")
# Imports
# -----------------------
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from deepface import DeepFace
import sqlite3
import os
import shutil
import json
from datetime import datetime
from typing import List
from repositories.registration_repo import RegistrationRepository
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# -----------------------
# App initialization
# -----------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")
print(f"[DEBUG] Using database file: {os.path.abspath(DB_PATH)}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["http://localhost:4200"] for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Room List with Floor Level Endpoint
# -----------------------
@app.get("/api/rooms/floors", tags=["Rooms"])
async def get_rooms_with_floors():
    print("[DEBUG] Entered /api/rooms/floors endpoint")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT room_id, floor_level, room_number FROM rooms")
        rows = cursor.fetchall()
        print(f"[DEBUG] /api/rooms/floors fetched rows: {rows}")
        rooms = [
            {"room_id": row[0], "floor_level": row[1], "room_number": row[2]}
            for row in rows
        ]
    return rooms

def migrate_classes_table():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='classes'")
        if cursor.fetchone():
            # Get current schema
            cursor.execute("PRAGMA table_info(classes)")
            columns = [row[1] for row in cursor.fetchall()]
            # Check for old unique constraint
            cursor.execute("PRAGMA index_list(classes)")
            indexes = cursor.fetchall()
            for idx in indexes:
                if idx[1] == 'sqlite_autoindex_classes_2':
                    # Drop the old table and recreate with new constraint
                    cursor.execute("ALTER TABLE classes RENAME TO classes_old")
                    cursor.execute("""
                        CREATE TABLE classes (
                            class_id VARCHAR(50) PRIMARY KEY,
                            course_code VARCHAR(20),
                            section VARCHAR(20),
                            room_id VARCHAR(20),
                            instructor_name VARCHAR(100),
                            day_of_week VARCHAR(10),
                            start_time TIME,
                            end_time TIME,
                            UNIQUE(course_code, section, room_id, day_of_week)
                        )
                    """)
                    cursor.execute("INSERT INTO classes (class_id, course_code, section, room_id, instructor_name, day_of_week, start_time, end_time) SELECT class_id, course_code, section, room_id, instructor_name, day_of_week, start_time, end_time FROM classes_old")
                    cursor.execute("DROP TABLE classes_old")
                    conn.commit()
                    break

migrate_classes_table()

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

app = FastAPI(openapi_tags=tags_metadata)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["http://localhost:4200"] for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



async def get_room_schedule(room: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT course_code, section, instructor_name, day_of_week, start_time, end_time
            FROM classes WHERE room_id = ?
        """, (room,))
        schedule = [
            {
                "courseCode": row[0],
                "section": row[1],
                "professor": row[2],
                "day": row[3],
                "startTime": row[4],
                "endTime": row[5]
            }
            for row in cursor.fetchall()
        ]
    return {"schedule": schedule}

@app.post("/api/room-schedule/{room}", tags=["Rooms"])
async def save_room_schedule(room: str, schedule: list = Body(...)):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Remove existing schedule for this room
        cursor.execute("DELETE FROM classes WHERE room_id = ?", (room,))
        # Insert new schedule
        for entry in schedule:
            cursor.execute("""
                INSERT INTO classes (class_id, course_code, section, room_id, instructor_name, day_of_week, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{entry.get('courseCode','')}_{entry.get('section','')}_{room}_{entry.get('day','')}_{entry.get('startTime','')}",
                entry.get('courseCode',''),
                entry.get('section',''),
                room,
                entry.get('professor',''),
                entry.get('day',''),
                entry.get('startTime',''),
                entry.get('endTime','')
            ))
        conn.commit()
    return {"status": "success"}

@app.delete("/api/room-schedule/{room}", tags=["Rooms"])
async def delete_room_schedule(room: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM classes WHERE room_id = ?", (room,))
        conn.commit()
    return {"status": "deleted"}



# -----------------------
# App initialization
# -----------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["http://localhost:4200"] for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Room, Course, Section Listing Endpoints
# -----------------------
@app.get("/api/rooms")
async def get_rooms():
    schedules_dir = "schedules"
    if not os.path.exists(schedules_dir):
        return []
    rooms = [f[:-5] for f in os.listdir(schedules_dir) if f.endswith(".json")]
    return rooms

@app.get("/api/courses")
async def get_courses(room: str):
    schedule_path = os.path.join("schedules", f"{room}.json")
    if not os.path.exists(schedule_path):
        return []
    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    courses = sorted(list(set(entry.get("courseCode") for entry in schedule if entry.get("courseCode"))))
    return courses

@app.get("/api/sections")
async def get_sections(room: str, course: str):
    schedule_path = os.path.join("schedules", f"{room}.json")
    if not os.path.exists(schedule_path):
        return []
    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    sections = sorted(list(set(entry.get("section") for entry in schedule if entry.get("courseCode") == course and entry.get("section"))))
    return sections

DB_PATH = "attendance.db"

# -----------------------
# Database setup
# -----------------------
def init_db():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS AttendanceLogs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id VARCHAR(20),
                class_id VARCHAR(20),
                timestamp DATETIME,
                attendance_date DATE,
                status VARCHAR(20),
                FOREIGN KEY(student_id) REFERENCES students(student_id),
                FOREIGN KEY(class_id) REFERENCES classes(class_id),
                UNIQUE(student_id, class_id, attendance_date)
            )
        ''')
with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                class_id VARCHAR(20) PRIMARY KEY,
                course_code VARCHAR(20),
                section VARCHAR(20),
                room_id VARCHAR(20),
                instructor_name VARCHAR(100),
                day_of_week VARCHAR(10),
                start_time TIME,
                end_time TIME,
                UNIQUE(course_code, section),
                FOREIGN KEY(room_id) REFERENCES rooms(room_id)
            )
        ''')
    # Removed old attendance table creation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE,
                last_name TEXT,
                first_name TEXT,
                email TEXT,
                face_data_path TEXT,
                created_at DATETIME
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                course_code TEXT,
                section TEXT,
                room TEXT,
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id VARCHAR(20) PRIMARY KEY,
                floor_level INTEGER,
                room_number VARCHAR(10)
            )
        ''')
        # Optionally, add columns to existing rooms table if they don't exist (for migrations)
        try:
            cursor.execute('ALTER TABLE rooms ADD COLUMN floor_level INTEGER')
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE rooms ADD COLUMN room_number VARCHAR(10)')
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.commit()
# Helper to extract floor level from room_id (e.g., '305' -> 3, '1201' -> 12)
def extract_floor_level(room_id: str) -> int:
    digits = ''.join([c for c in room_id if c.isdigit()])
    if not digits:
        return 0
    # If room_id is 3 or 4 digits, use first 1 or 2 digits as floor
    if len(digits) >= 4:
        return int(digits[:2])
    return int(digits[0])

# Helper to extract just the numeric room number (e.g., 'MPO305' -> '305')
def extract_room_number(room_id: str) -> str:
    digits = ''.join([c for c in room_id if c.isdigit()])
    return digits if digits else room_id

init_db()

# -----------------------
# Face Recognition
# -----------------------
@app.post("/api/recognize", tags=["Recognition"])
async def recognize_face(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...), room: str = Form(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    recognized_id = None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT student_id FROM student_courses
                WHERE course_code = ? AND section = ? AND (room = ? OR room IS NULL)
            ''', (course_code, section, room))
            student_ids = [row[0] for row in cursor.fetchall()]

            student_faces = {}
            for student_id in student_ids:
                student_folder = os.path.join("dataset", student_id)
                if os.path.isdir(student_folder):
                    images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.lower().endswith(".jpg")]
                    if images:
                        student_faces[student_id] = images[0]

            for student_id, img_path in student_faces.items():
                try:
                    result = DeepFace.verify(img1_path=temp_path, img2_path=img_path, model_name="ArcFace", enforce_detection=False)
                    distance = result.get('distance')
                    threshold = 0.3  # Stricter threshold for cosine distance (default is 0.68)
                    logging.info(f"Comparing temp image with {img_path} (student_id={student_id}): verified={result['verified']}, distance={distance}, threshold={threshold}")
                    if result["verified"] and distance is not None and distance < threshold:
                        # Find class_id for this course_code, section, and room
                        cursor.execute('''
                            SELECT class_id FROM classes
                            WHERE course_code = ? AND section = ? AND (room_id = ? OR room_id IS NULL)
                        ''', (course_code, section, room))
                        class_row = cursor.fetchone()
                        if class_row:
                            class_id = class_row[0]
                            # Check for duplicate attendance for today
                            cursor.execute('''
                                SELECT 1 FROM AttendanceLogs
                                WHERE student_id = ? AND class_id = ? AND attendance_date = DATE('now')
                            ''', (student_id, class_id))
                            if cursor.fetchone() is None:
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cursor.execute('''
                                    INSERT INTO AttendanceLogs (student_id, class_id, timestamp, attendance_date, image_path, status)
                                    VALUES (?, ?, ?, DATE('now'), ?, ?)
                                ''', (student_id, class_id, timestamp, temp_path, 'present'))
                                conn.commit()
                            recognized_id = student_id
                            break
                except Exception:
                    continue
    finally:
        os.remove(temp_path)

    if recognized_id:
        return {"status": "success", "student_id": recognized_id}
    else:
        return {"status": "failed", "message": "No match found"}

# -----------------------
# Image Capture
# -----------------------
@app.post("/api/capture", tags=["Capture"])
async def capture_image(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...), student_id: str = Form(...)):
    save_path = os.path.join("dataset", course_code, section, student_id)
    os.makedirs(save_path, exist_ok=True)
    img_path = os.path.join(save_path, file.filename)
    with open(img_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "message": f"Image saved to {img_path}"}

# -----------------------
# Attendance Retrieval
# -----------------------
@app.get("/api/attendance", tags=["Attendance"])
async def get_attendance(course_code: str, section: str, room: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Find class_id for this course_code, section, and room
        if room:
            cursor.execute('''
                SELECT class_id FROM classes
                WHERE course_code = ? AND section = ? AND (room_id = ? OR room_id IS NULL)
            ''', (course_code, section, room))
        else:
            cursor.execute('''
                SELECT class_id FROM classes
                WHERE course_code = ? AND section = ?
            ''', (course_code, section))
        class_row = cursor.fetchone()
        if not class_row:
            return {"attendance": []}
        class_id = class_row[0]
        cursor.execute('''
            SELECT student_id, timestamp, attendance_date, image_path, status FROM AttendanceLogs
            WHERE class_id = ?
        ''', (class_id,))
        rows = cursor.fetchall()
    return {"attendance": rows}



# Clear and re-insert schedule

# -----------------------
# Debug: List routes
# -----------------------
@app.get("/api/routes", tags=["Debug"])
async def list_routes():
    return [route.path for route in app.routes]
