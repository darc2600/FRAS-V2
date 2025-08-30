import sqlite3
import os
import shutil
from fastapi import UploadFile, HTTPException
from typing import List

DB_PATH = "attendance.db"

class RegistrationRepository:
    async def register_student(self, student_id: str, name: str, schedule_entries: list, images: List[UploadFile]):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO students (student_id, name)
                    VALUES (?, ?)
                ''', (student_id, name))
                conn.commit()
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail="Student ID already registered.")

            # Clear and re-insert schedule
            cursor.execute('DELETE FROM student_courses WHERE student_id = ?', (student_id,))
            for entry in schedule_entries:
                cursor.execute('''
                    INSERT INTO student_courses (student_id, course_code, section, room)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, entry.get("course_code"), entry.get("section"), entry.get("room")))
            conn.commit()

        # Save images under dataset/{student_id}/
        save_path = os.path.join("dataset", student_id)
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
