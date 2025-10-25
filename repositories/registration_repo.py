from services.db import get_connection
import os
import shutil
from fastapi import UploadFile, HTTPException
from typing import List
import sqlite3


class RegistrationRepository:
    async def register_student(self, student_number: str, last_name: str, first_name: str, email: str, created_at: str, schedule_entries: list, images: List[UploadFile]):
        face_data_path = os.path.join("dataset", student_number)

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                # Check if student already exists
                cursor.execute('SELECT student_id FROM students WHERE student_number = ?', (student_number,))
                existing_student = cursor.fetchone()

                if existing_student:
                    # Student already exists, return error
                    raise HTTPException(status_code=409, detail=f"Student with number '{student_number}' is already registered.")

                # Insert new student
                cursor.execute('''
                    INSERT INTO students (student_number, last_name, first_name, email, face_data_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (student_number, last_name, first_name, email, face_data_path, created_at))
                conn.commit()

                # Get the student_id (PK) for enrollments
                cursor.execute('SELECT student_id FROM students WHERE student_number = ?', (student_number,))
                row = cursor.fetchone()
                if row:
                    student_id = row[0]
                else:
                    raise HTTPException(status_code=500, detail="Student not found after insert.")

                # Clear and re-insert enrollments
                cursor.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))
                for entry in schedule_entries:
                    course_code = entry.get("course_code")
                    section = entry.get("section")

                    if not course_code or not section:
                        continue

                    # Get course_id from course_code
                    cursor.execute('SELECT course_id FROM courses WHERE course_code = ?', (course_code,))
                    course_row = cursor.fetchone()
                    if not course_row:
                        continue  # Skip if course not found
                    course_id = course_row[0]

                    # Find class that matches course_id and section
                    # Note: There might be multiple classes with same course_id and section
                    # For now, we'll take the first one found
                    cursor.execute('''
                        SELECT class_id FROM classes
                        WHERE course_id = ? AND section = ?
                        LIMIT 1
                    ''', (course_id, section))
                    class_row = cursor.fetchone()
                    if class_row:
                        class_id = class_row[0]
                        cursor.execute('''
                            INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)
                        ''', (student_id, class_id))
                conn.commit()

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

        # Save images under dataset/{student_number}/
        save_path = face_data_path
        os.makedirs(save_path, exist_ok=True)
        saved_files = []
        for file in images:
            img_path = os.path.join(save_path, file.filename)
            with open(img_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(img_path)

        return {"status": "success", "message": "Student registered and images saved.", "image_paths": saved_files}


def get_registration_repository():
    return RegistrationRepository()
