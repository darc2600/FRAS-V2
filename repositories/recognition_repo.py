import os
import shutil
from fastapi import UploadFile
from deepface import DeepFace
from datetime import datetime
from models.recognition import RecognitionResponse
from services.db import get_connection
from services.s3_utils import download_student_folder


class RecognitionRepository:
    async def recognize_face(self, file: UploadFile, class_id: int) -> RecognitionResponse:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        recognized_id = None
        recognized_name = None
        recognized_status = None
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all students enrolled in this class
                cursor.execute('''
                    SELECT e.student_id, s.student_number, s.face_data_path 
                    FROM enrollments e
                    JOIN students s ON e.student_id = s.student_id
                    WHERE e.class_id = ?
                ''', (class_id,))
                enrolled_students = cursor.fetchall()
                print(f"[DEBUG] Enrolled students in class {class_id}: {enrolled_students}")
                
                student_faces = {}
                for student_id, student_number, face_data_path in enrolled_students:
                    # Use the face_data_path from the database, or construct it
                    if face_data_path:
                        student_folder = face_data_path
                    else:
                        student_folder = os.path.join("dataset", str(student_number))
                    
                    # Check if folder exists locally
                    if not os.path.isdir(student_folder):
                        # Try to download from S3
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
                        student_faces[student_id] = images[0]  # Use first image for comparison
                
                print(f"[DEBUG] Student faces to compare: {student_faces}")
                
                # Compare faces
                for student_id, img_path in student_faces.items():
                    try:
                        print(f"[DEBUG] Comparing temp image {temp_path} with {img_path} for student {student_id}")
                        result = DeepFace.verify(img1_path=temp_path, img2_path=img_path, model_name="ArcFace", enforce_detection=False)
                        print(f"[DEBUG] DeepFace result for {student_id}: {result}")
                        if result["verified"]:
                            # Get class start_time for attendance status
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
                                # Try 24-hour format first (HH:MM)
                                class_start = datetime.strptime(attendance_date + ' ' + start_time_str, "%Y-%m-%d %H:%M")
                            except ValueError:
                                try:
                                    # Fall back to 12-hour format with AM/PM (HH:MMAM/PM)
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
                            
                            # Get student name for response
                            cursor.execute('''
                                SELECT last_name FROM students WHERE student_id = ?
                            ''', (student_id,))
                            name_row = cursor.fetchone()
                            student_name = name_row[0] if name_row else "Unknown"
                            
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
                                print(f"[DEBUG] Attendance logged for student {student_id} in class {class_id}")
                            
                            # Set recognized variables (always, even if attendance was already logged)
                            recognized_id = student_id
                            recognized_name = student_name
                            recognized_status = status
                            print(f"[DEBUG] Set recognized variables: id={recognized_id}, name={recognized_name}, status={recognized_status}")
                            break
                    except Exception as e:
                        print(f"[DEBUG] Exception for {student_id}: {e}")
                        continue
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass
        
        print(f"[DEBUG] About to return: recognized_id={recognized_id}, recognized_name={recognized_name}, recognized_status={recognized_status}")
        if recognized_id:
            print(f"[DEBUG] Returning success response: id={recognized_id}, name={recognized_name}, status={recognized_status}")
            return RecognitionResponse(
                status="success", 
                student_id=str(recognized_id),
                student_name=recognized_name,
                attendance_status=recognized_status
            )
        else:
            print(f"[DEBUG] Returning failure response: No match found")
            return RecognitionResponse(status="failed", message="No match found")


def get_recognition_repository():
    return RecognitionRepository()
