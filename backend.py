from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from deepface import DeepFace
import sqlite3
import os
from datetime import datetime
import shutil
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:4200"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
DB_PATH = "attendance.db"
conn = sqlite3.connect(DB_PATH)
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
conn.commit()
conn.close()

# Endpoint to recognize face
@app.post("/recognize")
async def recognize_face(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    dataset_path = os.path.join("dataset", course_code, section)
    student_faces = {}
    for student_id in os.listdir(dataset_path):
        student_folder = os.path.join(dataset_path, student_id)
        if os.path.isdir(student_folder):
            images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.endswith(".jpg")]
            if images:
                student_faces[student_id] = images[0]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    recognized_id = None
    for student_id, img_path in student_faces.items():
        try:
            result = DeepFace.verify(img1_path=temp_path, img2_path=img_path, model_name="ArcFace", enforce_detection=False)
            if result["verified"]:
                cursor.execute("""
                    SELECT * FROM attendance
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
        except Exception as e:
            continue

    conn.close()
    os.remove(temp_path)

    if recognized_id:
        return JSONResponse(content={"status": "success", "student_id": recognized_id})
    else:
        return JSONResponse(content={"status": "failed", "message": "No match found"})

# Endpoint to capture and save student image
@app.post("/capture")
async def capture_image(file: UploadFile = File(...), course_code: str = Form(...), section: str = Form(...), student_id: str = Form(...)):
    save_path = os.path.join("dataset", course_code, section, student_id)
    os.makedirs(save_path, exist_ok=True)
    img_path = os.path.join(save_path, file.filename)
    with open(img_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return JSONResponse(content={"status": "success", "message": f"Image saved to {img_path}"})

# Endpoint to get attendance logs
@app.get("/attendance")
async def get_attendance(course_code: str, section: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_id, timestamp FROM attendance
        WHERE course_code = ? AND section = ?
    """, (course_code, section))
    rows = cursor.fetchall()
    conn.close()
    return {"attendance": rows}
