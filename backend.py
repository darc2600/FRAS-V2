from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
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

DB_PATH = "attendance.db"

# -----------------------
# Database setup
# -----------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                course_code TEXT,
                section TEXT,
                timestamp TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE,
                name TEXT
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
        conn.commit()

init_db()

# -----------------------
# Face Recognition
# -----------------------
@app.post("/api/recognize")
async def recognize_face(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    recognized_id = None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT student_id FROM student_courses
                WHERE course_code = ? AND section = ?
            ''', (course_code, section))
            student_ids = [row[0] for row in cursor.fetchall()]

            student_faces = {}
            for student_id in student_ids:
                student_folder = os.path.join("dataset", course_code, section, student_id)
                if os.path.isdir(student_folder):
                    images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.lower().endswith(".jpg")]
                    if images:
                        student_faces[student_id] = images[0]

            for student_id, img_path in student_faces.items():
                try:
                    result = DeepFace.verify(img1_path=temp_path, img2_path=img_path, model_name="ArcFace", enforce_detection=False)
                    if result["verified"]:
                        cursor.execute("""
                            SELECT 1 FROM attendance
                            WHERE student_id = ? AND course_code = ? AND section = ? AND DATE(timestamp) = DATE('now')
                        """, (student_id, course_code, section))
                        if cursor.fetchone() is None:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            cursor.execute("""
                                INSERT INTO attendance (student_id, course_code, section, timestamp)
                                VALUES (?, ?, ?, ?)
                            """, (student_id, course_code, section, timestamp))
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
@app.post("/api/capture")
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
@app.get("/api/attendance")
async def get_attendance(course_code: str, section: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_id, timestamp FROM attendance
            WHERE course_code = ? AND section = ?
        """, (course_code, section))
        rows = cursor.fetchall()
    return {"attendance": rows}

# -----------------------
# Student Registration
# -----------------------
@app.post("/api/registration")
async def register_student(
    student_id: str = Form(...),
    name: str = Form(...),
    schedule: str = Form(...),  # JSON list of {course_code, section, room}
    images: List[UploadFile] = File(...)
):
    try:
        schedule_entries = json.loads(schedule)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid schedule: {e}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO students (student_id, name)
                VALUES (?, ?)
            ''', (student_id, name))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Student ID already registered.")

        # Clear and re-insert schedule
        cursor.execute('DELETE FROM student_courses WHERE student_id = ?', (student_id,))
        for entry in schedule_entries:
            cursor.execute('''
                INSERT INTO student_courses (student_id, course_code, section, room)
                VALUES (?, ?, ?, ?)
            ''', (student_id, entry.get("course_code"), entry.get("section"), entry.get("room")))
        conn.commit()

    # Save images
    saved_files = []
    for file in images:
        save_path = os.path.join("dataset", entry.get("course_code"), entry.get("section"), student_id)
        os.makedirs(save_path, exist_ok=True)
        img_path = os.path.join(save_path, file.filename)
        with open(img_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(img_path)

    return {"status": "success", "message": "Student registered and images saved.", "image_paths": saved_files}

# -----------------------
# Room Schedule Endpoints
# -----------------------
@app.get("/api/room-schedule/{room_code}")
async def get_room_schedule(room_code: str):
    schedule_path = os.path.join("schedules", f"{room_code}.json")
    if not os.path.exists(schedule_path):
        raise HTTPException(status_code=404, detail="Room schedule not found")
    with open(schedule_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/room-schedule/{room_code}")
async def update_room_schedule(room_code: str, request: Request):
    os.makedirs("schedules", exist_ok=True)
    schedule_path = os.path.join("schedules", f"{room_code}.json")
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        schedule = await request.json()
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        schedule_str = form.get("schedule")
        if not schedule_str:
            raise HTTPException(status_code=400, detail="Missing 'schedule' field in form data.")
        try:
            schedule = json.loads(schedule_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON in 'schedule' field.")
    else:
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(jsonable_encoder(schedule), f, ensure_ascii=False, indent=2)

    return {"status": "success", "message": f"Schedule for {room_code} updated."}

# -----------------------
# Debug: List routes
# -----------------------
@app.get("/api/routes")
async def list_routes():
    return [route.path for route in app.routes]
