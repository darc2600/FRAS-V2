import sqlite3
import os
from services.db import get_connection

with get_connection() as conn:
    cursor = conn.cursor()

# Get all students
cursor.execute('SELECT student_id, student_number FROM students')
students = cursor.fetchall()

count = 0
for student_id, student_number in students:
    # Check if dataset folder exists for this student
    face_data_path = os.path.join("dataset", str(student_number))
    
    if os.path.isdir(face_data_path):
        # Update the face_data_path in database
        cursor.execute('''
            UPDATE students 
            SET face_data_path = ? 
            WHERE student_id = ?
        ''', (face_data_path, student_id))
        count += 1
        print(f'Updated {student_number}: {face_data_path}')

    # commit handled by connection wrapper
    print(f'\nTotal updated: {count} students')
