import sqlite3
import os
import shutil
from fastapi import UploadFile, HTTPException
from typing import List

DB_PATH = "attendance.db"

class RegistrationRepository:
    async def register_student(self, student_id: str, last_name: str, first_name: str, email: str, created_at: str, schedule_entries: list, images: List[UploadFile]):
        face_data_path = os.path.join("dataset", student_id)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Upsert student info: update if exists, insert if not
            cursor.execute('''
                INSERT INTO students (student_id, last_name, first_name, email, face_data_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                    last_name=excluded.last_name,
                    first_name=excluded.first_name,
                    email=excluded.email,
                    face_data_path=excluded.face_data_path,
                    created_at=excluded.created_at
            ''', (student_id, last_name, first_name, email, face_data_path, created_at))
            conn.commit()

            # Clear and re-insert schedule
            cursor.execute('DELETE FROM student_courses WHERE student_id = ?', (student_id,))
            for entry in schedule_entries:
                cursor.execute('''
                    INSERT INTO student_courses (student_id, course_code, section, room)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, entry.get("course_code"), entry.get("section"), entry.get("room")))
            conn.commit()

        # Save images under dataset/{student_id}/
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
