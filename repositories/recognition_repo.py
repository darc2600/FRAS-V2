import os
import shutil
from fastapi import UploadFile
from deepface import DeepFace
from datetime import datetime
from models.recognition import RecognitionResponse
from services.db import get_connection
from services.s3_utils import download_student_folder
from services.settings_service import get_settings_service


class RecognitionRepository:
    def __init__(self):
        self.settings = get_settings_service()

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

                        # Use settings for face recognition parameters
                        model_name = self.settings.face_recognition_model
                        threshold = self.settings.recognition_threshold
                        enforce_detection = self.settings.face_detection_confidence > 0.5  # Convert to boolean

                        result = DeepFace.verify(
                            img1_path=temp_path,
                            img2_path=img_path,
                            model_name=model_name,
                            enforce_detection=enforce_detection,
                            threshold=threshold
                        )
                        print(f"[DEBUG] DeepFace result for {student_id}: {result}")
                        if result["verified"]:
                            # Get class details for attendance status
                            cursor.execute('''
                                SELECT day_of_week, start_time, end_time FROM classes WHERE class_id = ?
                            ''', (class_id,))
                            class_row = cursor.fetchone()
                            if not class_row:
                                print(f"[DEBUG] No class details found for class_id={class_id}")
                                continue
                            day_of_week, start_time_str, end_time_str = class_row
                            
                            # Parse times
                            now = datetime.now()
                            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                            attendance_date = now.strftime("%Y-%m-%d")
                            current_day = now.strftime("%A")  # e.g., "Monday"
                            
                            # Check if today is the class day
                            if current_day != day_of_week:
                                print(f"[DEBUG] Not class day: today={current_day}, class_day={day_of_week}")
                                continue
                            
                            # Convert start_time and end_time to datetime for today
                            try:
                                # Try 24-hour format first (HH:MM)
                                class_start = datetime.strptime(attendance_date + ' ' + start_time_str, "%Y-%m-%d %H:%M")
                                class_end = datetime.strptime(attendance_date + ' ' + end_time_str, "%Y-%m-%d %H:%M")
                            except ValueError:
                                try:
                                    # Fall back to 12-hour format with AM/PM (HH:MMAM/PM)
                                    class_start = datetime.strptime(attendance_date + ' ' + start_time_str, "%Y-%m-%d %I:%M%p")
                                    class_end = datetime.strptime(attendance_date + ' ' + end_time_str, "%Y-%m-%d %I:%M%p")
                                except Exception as e:
                                    print(f"[DEBUG] Could not parse start_time or end_time: {e}")
                                    continue
                            
                            # Check if current time is within class hours
                            if not (class_start <= now <= class_end):
                                print(f"[DEBUG] Outside class hours: now={now}, class_start={class_start}, class_end={class_end}")
                                continue
                            
                            delta = (now - class_start).total_seconds() / 60.0

                            # Use configurable attendance thresholds from settings
                            late_threshold = self.settings.late_threshold_minutes
                            absent_threshold = self.settings.absent_threshold_minutes

                            if 0 <= delta <= late_threshold:
                                status_name = "Present"
                                print(f"[DEBUG] Marked as Present: delta={delta:.2f} mins since class start (<= {late_threshold} mins)")
                            elif late_threshold < delta <= absent_threshold:
                                status_name = "Late"
                                print(f"[DEBUG] Marked as Late: delta={delta:.2f} mins since class start ({late_threshold}-{absent_threshold} mins)")
                            else:
                                status_name = "Absent"
                                print(f"[DEBUG] Marked as Absent: delta={delta:.2f} mins since class start (> {absent_threshold} mins)")
                            
                            # Get status_id from attendance_status_types table
                            cursor.execute('''
                                SELECT status_id FROM attendance_status_types WHERE status_name = ?
                            ''', (status_name,))
                            status_row = cursor.fetchone()
                            if not status_row:
                                print(f"[DEBUG] No status_id found for status_name={status_name}")
                                continue
                            status_id = status_row[0]
                            
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
                                    INSERT INTO attendance_logs (student_id, class_id, timestamp, status_id)
                                    VALUES (?, ?, ?, ?)
                                """, (student_id, class_id, timestamp, status_id))
                                conn.commit()
                                print(f"[DEBUG] Attendance logged for student {student_id} in class {class_id}")
                            
                            # Set recognized variables (always, even if attendance was already logged)
                            recognized_id = student_id
                            recognized_name = student_name
                            recognized_status = status_name
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

    async def mark_absents(self, class_id: int, date: str):
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all enrolled students for the class
            cursor.execute('''
                SELECT e.student_id, s.last_name
                FROM enrollments e
                JOIN students s ON e.student_id = s.student_id
                WHERE e.class_id = ?
            ''', (class_id,))
            enrolled_students = cursor.fetchall()
            
            # Get students who already have attendance for the date
            cursor.execute('''
                SELECT DISTINCT student_id FROM attendance_logs
                WHERE class_id = ? AND DATE(timestamp) = ?
            ''', (class_id, date))
            attended_students = {row[0] for row in cursor.fetchall()}
            
            # Get absent status_id
            cursor.execute('''
                SELECT status_id FROM attendance_status_types WHERE status_name = 'Absent'
            ''')
            status_row = cursor.fetchone()
            if not status_row:
                return {"error": "Absent status not found"}
            absent_status_id = status_row[0]
            
            absent_count = 0
            for student_id, last_name in enrolled_students:
                if student_id not in attended_students:
                    # Insert absent record
                    timestamp = f"{date} 23:59:59"  # End of day
                    cursor.execute('''
                        INSERT INTO attendance_logs (student_id, class_id, timestamp, status_id)
                        VALUES (?, ?, ?, ?)
                    ''', (student_id, class_id, timestamp, absent_status_id))
                    absent_count += 1
                    print(f"[DEBUG] Marked student {student_id} ({last_name}) as Absent for class {class_id} on {date}")
            
            conn.commit()
            return {"message": f"Marked {absent_count} students as absent for class {class_id} on {date}"}


def get_recognition_repository():
    return RecognitionRepository()
