import sqlite3
import os
import shutil
from fastapi import UploadFile, HTTPException
from typing import List

DB_PATH = "attendance.db"

class RegistrationRepository:
    async def register_student(self, student_number: str, last_name: str, first_name: str, email: str, created_at: str, schedule_entries: list, images: List[UploadFile]):
        face_data_path = os.path.join("dataset", student_number)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Upsert student info: update if exists, insert if not
            cursor.execute('''
                INSERT INTO students (student_number, last_name, first_name, email, face_data_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_number) DO UPDATE SET
                    last_name=excluded.last_name,
                    first_name=excluded.first_name,
                    email=excluded.email,
                    face_data_path=excluded.face_data_path,
                    created_at=excluded.created_at
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
                room_id = entry.get("room")
                # Lookup class_id from classes
                cursor.execute('''
                    SELECT class_id FROM classes WHERE course_code = ? AND section = ? AND room_id = ?
                ''', (course_code, section, room_id))
                class_row = cursor.fetchone()
                if class_row:
                    class_id = class_row[0]
                    cursor.execute('''
                        INSERT INTO enrollments (student_id, class_id) VALUES (?, ?)
                    ''', (student_id, class_id))
            conn.commit()

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
