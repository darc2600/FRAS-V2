from services.db import get_connection
import os
import shutil
from fastapi import UploadFile, HTTPException
from typing import List
import sqlite3


class RegistrationRepository:
    async def register_student(self, student_number: str, last_name: str, first_name: str, email: str, created_at: str, schedule_entries: list, images: List[UploadFile]):
        print(f"[DEBUG] ========== REGISTRATION START ==========")
        print(f"[DEBUG] Student Number: {student_number}")
        print(f"[DEBUG] Repo called with schedule_entries: {schedule_entries}, len: {len(schedule_entries) if schedule_entries else 'None'}")
        face_data_path = os.path.join("dataset", student_number)
        print(f"[DEBUG] Face data path set to: {face_data_path}")
        update_existing = False

        conn = get_connection()
        try:
            cursor = conn.cursor()
            # Check if student already exists
            cursor.execute('SELECT student_id, face_data_path FROM students WHERE student_number = ?', (student_number,))
            existing_student = cursor.fetchone()

            if existing_student:
                student_id, existing_face_data_path = existing_student
                print(f"[DEBUG] Student already exists - student_id: {student_id}, existing_face_data_path: {existing_face_data_path}")
                # Student exists, allow saving face data
                update_existing = True
            else:
                print(f"[DEBUG] Student does not exist, creating new student")
                update_existing = False

                if not update_existing:
                    # Insert new student
                    print(f"[DEBUG] Inserting new student with face_data_path: {face_data_path}")
                    cursor.execute('''
                        INSERT INTO students (student_number, last_name, first_name, email, face_data_path, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (student_number, last_name, first_name, email, face_data_path, created_at))
                    conn.commit()
                    print(f"[DEBUG] Student inserted successfully")

                    # Get the student_id (PK) for enrollments
                    cursor.execute('SELECT student_id FROM students WHERE student_number = ?', (student_number,))
                    row = cursor.fetchone()
                    if row:
                        student_id = row[0]
                        print(f"[DEBUG] Retrieved student_id: {student_id}")
                    else:
                        raise HTTPException(status_code=500, detail="Student not found after insert.")

            if schedule_entries:
                # Clear and re-insert enrollments
                print(f"[DEBUG] Clearing existing enrollments for student_id: {student_id}")
                cursor.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))
                print(f"[DEBUG] Registering student {student_number} with schedule_entries: {schedule_entries}")
                print(f"[DEBUG] Total schedule entries to process: {len(schedule_entries)}")
                
                for idx, entry in enumerate(schedule_entries):
                    print(f"[DEBUG] Processing schedule entry {idx+1}/{len(schedule_entries)}: {entry}")
                    course_code = entry.get("course_code")
                    section = entry.get("section")

                    if not course_code or not section:
                        print(f"[DEBUG] Skipping entry with missing course_code or section: {entry}")
                        continue

                    # Get course_id from course_code
                    cursor.execute('SELECT course_id FROM courses WHERE UPPER(course_code) = UPPER(?)', (course_code,))
                    course_row = cursor.fetchone()
                    if not course_row:
                        print(f"[DEBUG] Course not found for course_code: {course_code}")
                        continue  # Skip if course not found
                    course_id = course_row[0]
                    print(f"[DEBUG] Found course_id {course_id} for {course_code}")

                    # Find class that matches course_id and section
                    cursor.execute('''
                        SELECT class_id FROM classes
                        WHERE course_id = ? AND UPPER(section) = UPPER(?)
                        LIMIT 1
                    ''', (course_id, section))
                    class_row = cursor.fetchone()
                    if class_row:
                        class_id = class_row[0]
                        print(f"[DEBUG] Found class_id {class_id} for course_id {course_id} section {section}")
                        cursor.execute('''
                            INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)
                        ''', (student_id, class_id))
                        print(f"[DEBUG] Inserted enrollment: student_id {student_id}, class_id {class_id}")
                    else:
                        print(f"[DEBUG] No class found for course_id {course_id} section {section}")
                try:
                    conn.commit()
                    print(f"[DEBUG] Enrollment committed for student {student_id}")
                except Exception as e:
                    print(f"[DEBUG] Commit failed: {e}")
                    raise
            else:
                print(f"[DEBUG] No schedule_entries provided for student {student_number}, skipping enrollment")

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(status_code=409, detail=f"Student with number '{student_number}' is already registered.")
            else:
                raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except HTTPException:
            # Re-raise HTTPException without wrapping it
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {e}")

        try:
            # Save images under dataset/{student_number}/
            save_path = face_data_path
            print(f"[DEBUG] Saving images to {save_path}")
            print(f"[DEBUG] Absolute path: {os.path.abspath(save_path)}")
            os.makedirs(save_path, exist_ok=True)
            print(f"[DEBUG] Directory created/confirmed at: {os.path.abspath(save_path)}")
            
            # Remove existing images if updating
            if update_existing:
                print(f"[DEBUG] Removing existing images for update")
                if os.path.exists(save_path):
                    for file in os.listdir(save_path):
                        file_path = os.path.join(save_path, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            print(f"[DEBUG] Removed {file_path}")
            
            saved_files = []
            total_images = len(images) if images else 0
            print(f"[DEBUG] Total images to save: {total_images}")
            
            for i, file in enumerate(images):
                print(f"[DEBUG] Processing image {i+1}/{total_images}: {file.filename}")
                try:
                    img_path = os.path.join(save_path, file.filename or f"image_{i}.jpg")
                    print(f"[DEBUG] Full image path: {os.path.abspath(img_path)}")
                    with open(img_path, "wb") as buffer:
                        content = file.file.read()
                        buffer.write(content)
                    saved_files.append(img_path)
                    print(f"[DEBUG] Successfully saved {img_path}")
                except Exception as e:
                    print(f"[DEBUG] Error saving {file.filename}: {e}")
                    raise

            # Verify images were saved
            print(f"[DEBUG] Verifying images were saved...")
            if os.path.exists(save_path):
                actual_files = os.listdir(save_path)
                print(f"[DEBUG] Files in {save_path}: {actual_files}")
            else:
                print(f"[DEBUG] ERROR: Directory does not exist after saving: {save_path}")
            
            # Update database with face_data_path if needed (for existing students or to confirm)
            print(f"[DEBUG] Updating database with face_data_path for student_id: {student_id}")
            try:
                cursor.execute('''
                    UPDATE students 
                    SET face_data_path = ? 
                    WHERE student_id = ?
                ''', (face_data_path, student_id))
                conn.commit()
                print(f"[DEBUG] Database updated - face_data_path set to: {face_data_path}")
            except Exception as e:
                print(f"[DEBUG] Error updating database: {e}")
                raise

            # Verify the update
            cursor.execute('SELECT face_data_path FROM students WHERE student_id = ?', (student_id,))
            db_result = cursor.fetchone()
            if db_result:
                db_face_path = db_result[0]
                print(f"[DEBUG] VERIFICATION - face_data_path in database: {db_face_path}")
                if db_face_path is None:
                    print(f"[DEBUG] WARNING: face_data_path is still NULL in database!")
                else:
                    print(f"[DEBUG] SUCCESS: face_data_path is properly set in database")
            else:
                print(f"[DEBUG] ERROR: Student record not found in database!")

            print(f"[DEBUG] Registration complete for {student_number}")
            print(f"[DEBUG] ========== REGISTRATION END ==========")
            if update_existing:
                return {"status": "success", "message": "Student face data updated successfully.", "image_paths": saved_files}
            else:
                return {"status": "success", "message": "Student registered and images saved.", "image_paths": saved_files}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {e}")
        finally:
            conn.close()

def get_registration_repository():
    return RegistrationRepository()
