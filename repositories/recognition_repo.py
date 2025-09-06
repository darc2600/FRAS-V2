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
                            # Find class_id for this attendance
                            cursor.execute('''
                                SELECT class_id FROM classes
                                WHERE course_code = ? AND section = ? AND room_id = ?
                            ''', (course_code, section, room))
                            class_row = cursor.fetchone()
                            if not class_row:
                                print(f"[DEBUG] No class_id found for course_code={course_code}, section={section}, room={room}")
                                continue
                            class_id = class_row[0]
                            # Get class start_time
                            cursor.execute('''
                                SELECT start_time FROM classes WHERE class_id = ?
                            ''', (class_id,))
                            class_time_row = cursor.fetchone()
                            if not class_time_row:
                                print(f"[DEBUG] No start_time found for class_id={class_id}")
                                continue
                            start_time_str = class_time_row[0]  # e.g., '07:00AM'
                            # Parse times
                            now = datetime.now()
                            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                            attendance_date = now.strftime("%Y-%m-%d")
                            # Convert start_time to datetime for today
                            try:
                                class_start = datetime.strptime(attendance_date + ' ' + start_time_str, "%Y-%m-%d %I:%M%p")
                            except Exception as e:
                                print(f"[DEBUG] Could not parse start_time: {e}")
                                continue
                            delta = (now - class_start).total_seconds() / 60.0
                            if 0 <= delta <= 30:
                                status = "Present"
                                print(f"[DEBUG] Marked as Present: delta={delta:.2f} mins since class start (<= 30 mins)")
                            else:
                                status = "Late"
                                print(f"[DEBUG] Marked as Late: delta={delta:.2f} mins since class start (> 30 mins)")
                            # Check for duplicate attendance
                            cursor.execute("""
                                SELECT 1 FROM AttendanceLogs
                                WHERE student_id = ? AND class_id = ? AND attendance_date = ?
                            """, (student_id, class_id, attendance_date))
                            if cursor.fetchone() is None:
                                cursor.execute("""
                                    INSERT INTO AttendanceLogs (student_id, class_id, timestamp, attendance_date, status)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (student_id, class_id, timestamp, attendance_date, status))
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
