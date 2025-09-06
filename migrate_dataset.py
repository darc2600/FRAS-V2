import os
import shutil
import sqlite3

# Path to dataset and database
DATASET_DIR = 'dataset'
DB_PATH = 'attendance.db'

# Connect to DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def ensure_student(student_id):
    cursor.execute('INSERT OR IGNORE INTO students (student_id, name) VALUES (?, ?)', (student_id, student_id))
    conn.commit()

def add_student_course(student_id, course_code, section, room):
    cursor.execute('''
        INSERT INTO student_courses (student_id, course_code, section, room)
        VALUES (?, ?, ?, ?)
    ''', (student_id, course_code, section, room))
    conn.commit()

def migrate_flat():
    # Handles dataset/{student_id}/imgX.jpg
    for student_id in os.listdir(DATASET_DIR):
        student_path = os.path.join(DATASET_DIR, student_id)
        if os.path.isdir(student_path) and all(f.endswith('.jpg') for f in os.listdir(student_path)):
            ensure_student(student_id)
            # No course/section/room info for flat structure
            print(f"Flat: {student_id}")

def migrate_nested():
    # Handles dataset/{course_code}/{section}/{student_id}/imgX.jpg
    for course_code in os.listdir(DATASET_DIR):
        course_path = os.path.join(DATASET_DIR, course_code)
        if not os.path.isdir(course_path):
            continue
        for section in os.listdir(course_path):
            section_path = os.path.join(course_path, section)
            if not os.path.isdir(section_path):
                continue
            for student_id in os.listdir(section_path):
                student_path = os.path.join(section_path, student_id)
                if not os.path.isdir(student_path):
                    continue
                # Move images to dataset/{student_id}/
                new_student_dir = os.path.join(DATASET_DIR, student_id)
                os.makedirs(new_student_dir, exist_ok=True)
                for img in os.listdir(student_path):
                    src = os.path.join(student_path, img)
                    dst = os.path.join(new_student_dir, img)
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                ensure_student(student_id)
                add_student_course(student_id, course_code, section, room=None)
                print(f"Nested: {course_code}/{section}/{student_id}")

def migrate_deep_nested():
    # Handles dataset/{course_code}/{section}/{room}/{student_id}/imgX.jpg
    for course_code in os.listdir(DATASET_DIR):
        course_path = os.path.join(DATASET_DIR, course_code)
        if not os.path.isdir(course_path):
            continue
        for section in os.listdir(course_path):
            section_path = os.path.join(course_path, section)
            if not os.path.isdir(section_path):
                continue
            for room in os.listdir(section_path):
                room_path = os.path.join(section_path, room)
                if not os.path.isdir(room_path):
                    continue
                for student_id in os.listdir(room_path):
                    student_path = os.path.join(room_path, student_id)
                    if not os.path.isdir(student_path):
                        continue
                    new_student_dir = os.path.join(DATASET_DIR, student_id)
                    os.makedirs(new_student_dir, exist_ok=True)
                    for img in os.listdir(student_path):
                        src = os.path.join(student_path, img)
                        dst = os.path.join(new_student_dir, img)
                        if not os.path.exists(dst):
                            shutil.move(src, dst)
                    ensure_student(student_id)
                    add_student_course(student_id, course_code, section, room)
                    print(f"Deep: {course_code}/{section}/{room}/{student_id}")

def main():
    migrate_flat()
    migrate_nested()
    migrate_deep_nested()
    print("Migration complete.")

if __name__ == '__main__':
    main()
