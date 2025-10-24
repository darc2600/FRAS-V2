import os
import shutil
from fastapi import UploadFile
from deepface import DeepFace
from datetime import datetime
from models.recognition import RecognitionResponse
from services.db import get_connection
from services.s3_utils import download_student_folder


class RecognitionRepository:
    async def recognize_face(self, file: UploadFile, course_code: str, section: str, room: str) -> RecognitionResponse:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        recognized_id = None
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                # Lookup students enrolled in the class (by course_code, section, room_id)
                cursor.execute('''
                    SELECT e.student_id FROM enrollments e
                    JOIN classes c ON e.class_id = c.class_id
                    WHERE c.course_code = ? AND c.section = ? AND c.room_id = ?
                ''', (course_code, section, room))
                student_ids = [row[0] for row in cursor.fetchall()]
                print(f"[DEBUG] student_ids: {student_ids}")
                student_faces = {}
                for student_id in student_ids:
                    # Lookup student_number for this student_id
                    cursor.execute('SELECT student_number FROM students WHERE student_id = ?', (student_id,))
                    row = cursor.fetchone()
                    if not row:
                        continue
                    student_number = row[0]
                    student_folder = os.path.join("dataset", str(student_number))
                    # If local folder missing, try to download from S3 into a temp dir
                    if not os.path.isdir(student_folder):
                        tmpdir = os.path.join("/tmp", f"dataset_{student_number}") if os.name != 'nt' else os.path.join("C:\\Windows\\Temp", f"dataset_{student_number}")
                        os.makedirs(tmpdir, exist_ok=True)
                        try:
                            download_student_folder('fras-data', f'dataset/{student_number}/', tmpdir)
                            images = [os.path.join(tmpdir, img) for img in os.listdir(tmpdir) if img.lower().endswith('.jpg')]
                        except Exception:
                            images = []
                    else:
                        images = [os.path.join(student_folder, img) for img in os.listdir(student_folder) if img.lower().endswith('.jpg')]
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
                                SELECT 1 FROM attendance_logs
                                WHERE student_id = ? AND class_id = ? AND DATE(timestamp) = ?
                            """, (student_id, class_id, attendance_date))
                            if cursor.fetchone() is None:
                                cursor.execute("""
                                    INSERT INTO attendance_logs (student_id, class_id, timestamp, status)
                                    VALUES (?, ?, ?, ?)
                                """, (student_id, class_id, timestamp, status))
                                conn.commit()
                            recognized_id = student_id
                            break
                    except Exception as e:
                        print(f"[DEBUG] Exception for {student_id}: {e}")
                        continue
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass
        if recognized_id:
            return RecognitionResponse(status="success", student_id=str(recognized_id))
        else:
            return RecognitionResponse(status="failed", message="No match found")


def get_recognition_repository():
    return RecognitionRepository()
