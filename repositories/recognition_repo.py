import os
import shutil
import sqlite3
from fastapi import UploadFile
from deepface import DeepFace
from datetime import datetime
from models.recognition import RecognitionResponse

DB_PATH = "attendance.db"

class RecognitionRepository:
    async def recognize_face(self, file: UploadFile, course_code: str, section: str, room: str) -> RecognitionResponse:
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
                print(f"[DEBUG] student_ids: {student_ids}")
                student_faces = {}
                for student_id in student_ids:
                    student_folder = os.path.join("dataset", student_id)
                    if os.path.isdir(student_folder):
                        images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.lower().endswith(".jpg")]
                        if images:
                            student_faces[student_id] = images[0]
                print(f"[DEBUG] student_faces: {student_faces}")
                for student_id, img_path in student_faces.items():
                    try:
                        print(f"[DEBUG] Comparing temp image {temp_path} with {img_path} for student {student_id}")
                        result = DeepFace.verify(img1_path=temp_path, img2_path=img_path, model_name="ArcFace", enforce_detection=False)
                        print(f"[DEBUG] DeepFace result for {student_id}: {result}")
                        if result["verified"]:
                            cursor.execute("""
                                SELECT 1 FROM attendance
                                WHERE student_id = ? AND course_code = ? AND section = ? AND room = ? AND DATE(timestamp) = DATE('now')
                            """, (student_id, course_code, section, room))
                            if cursor.fetchone() is None:
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cursor.execute("""
                                    INSERT INTO attendance (student_id, course_code, section, room, timestamp)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (student_id, course_code, section, room, timestamp))
                                conn.commit()
                            recognized_id = student_id
                            break
                    except Exception as e:
                        print(f"[DEBUG] Exception for {student_id}: {e}")
                        continue
        finally:
            os.remove(temp_path)
        if recognized_id:
            return RecognitionResponse(status="success", student_id=recognized_id)
        else:
            return RecognitionResponse(status="failed", message="No match found")

def get_recognition_repository():
    return RecognitionRepository()
