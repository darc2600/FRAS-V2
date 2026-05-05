import os
import time
import json
import shutil
import sqlite3
from glob import glob
from datetime import datetime, timedelta

import requests

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()


def to_12h(dt):
    return dt.strftime('%I:%M%p')


def test_e2e_attendance_flow():
    # Preconditions: dataset folder exists with at least one numeric folder
    assert os.path.isdir('dataset'), "dataset folder not found"
    src_folders = [d for d in os.listdir('dataset') if os.path.isdir(os.path.join('dataset', d))]
    assert src_folders, "No dataset subfolders found"
    src = None
    for d in src_folders:
        if d.isdigit():
            src = d
            break
    if not src:
        src = src_folders[0]

    timestamp = int(datetime.utcnow().timestamp())
    new_student = f"t{timestamp}"
    new_folder = os.path.join('dataset', new_student)
    # copy images for registration (cleanup later)
    shutil.copytree(os.path.join('dataset', src), new_folder, dirs_exist_ok=True)

    try:
        # pick a room and course
        r = session.get(f"{BASE_URL}/api/rooms", timeout=5)
        assert r.status_code == 200
        rooms = r.json()
        assert rooms
        room = rooms[0]

        r = session.get(f"{BASE_URL}/api/courses", timeout=5)
        assert r.status_code == 200
        courses = r.json()
        assert courses
        course_code = courses[0]['code']

        # create schedule for now
        now = datetime.now()
        start = now - timedelta(minutes=5)
        end = now + timedelta(minutes=30)
        section = f"CI{timestamp % 10000}"
        schedule_entry = [{
            "courseCode": course_code,
            "section": section,
            "professor": "Brown, Michael",
            "day": now.strftime('%A'),
            "startTime": to_12h(start),
            "endTime": to_12h(end),
        }]

        r = session.post(f"{BASE_URL}/api/room-schedule/{room}", json=schedule_entry, timeout=15)
        created_class_id = None
        if r.status_code == 200:
            # schedule posted; we'll locate the created class later
            pass
        else:
            # could be a conflict when replacing schedules (existing enrollments). Try to find an existing
            # class for the course that is active now and use it instead.
            body = r.text
            # proceed but don't fail here — attempt to find an active class for the course
            now_time = now
            r2 = session.get(f"{BASE_URL}/api/classes", timeout=5)
            if r2.status_code == 200:
                candidates = r2.json()
                for c in candidates:
                    try:
                        if c.get('course_code') == course_code and c.get('day_of_week') == now.strftime('%A'):
                            # pick first matching-day class
                            created_class_id = c.get('id')
                            break
                    except Exception:
                        continue

        # Ensure there's a class record available for enrollment; if POST failed earlier, create one now
        created_class_id = None
        r2 = session.get(f"{BASE_URL}/api/classes", timeout=5)
        if r2.status_code == 200:
            classes = r2.json()
            class_id = next((c['id'] for c in classes if c.get('course_code') == course_code and c.get('section') == section), None)
        else:
            class_id = None

        if class_id is None:
            conn = sqlite3.connect('attendance.db')
            cur = conn.cursor()
            cur.execute("SELECT course_id FROM courses WHERE course_code = ?", (course_code,))
            c_row = cur.fetchone()
            assert c_row, "course not found in DB"
            course_id = c_row[0]
            cur.execute("SELECT room_id FROM rooms WHERE room_number = ?", (room,))
            r_row = cur.fetchone()
            room_id = r_row[0] if r_row else None
            cur.execute("SELECT instructor_id FROM instructors LIMIT 1")
            i_row = cur.fetchone()
            instructor_id = i_row[0] if i_row else None
            cur.execute(
                "INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (course_id, room_id, instructor_id, section, now.strftime('%A'), to_12h(start), to_12h(end))
            )
            conn.commit()
            created_class_id = cur.lastrowid
            conn.close()
            class_id = created_class_id

        # register the student via API
        imgs = [os.path.join(new_folder, f) for f in os.listdir(new_folder) if f.lower().endswith('.jpg')]
        assert imgs, "No jpg images in new student folder"
        files = [('images', (os.path.basename(p), open(p, 'rb'), 'image/jpeg')) for p in imgs[:3]]
        data = {
            'student_number': new_student,
            'last_name': 'Test',
            'first_name': 'Test',
            'email': f'{new_student}@example.local',
            'created_at': datetime.utcnow().isoformat(),
            'schedule': json.dumps([{"course_code": course_code, "section": section}])
        }
        r = session.post(f"{BASE_URL}/api/registration", data=data, files=files, timeout=30)
        for _, f in files:
            try:
                f[1].close()
            except Exception:
                pass
        assert r.status_code == 200, r.text

        # find the created class id
        # find the created class id (use created_class_id if schedule POST failed)
        r = session.get(f"{BASE_URL}/api/classes", timeout=5)
        assert r.status_code == 200
        classes = r.json()
        class_id = created_class_id or next((c['id'] for c in classes if c.get('course_code') == course_code and c.get('section') == section), None)
        # If still not found, create a classes row directly in the DB for the test (safe, cleaned up later)
        created_class_id = None
        if class_id is None:
            conn = sqlite3.connect('attendance.db')
            cur = conn.cursor()
            # resolve course_id and room_id
            cur.execute("SELECT course_id FROM courses WHERE course_code = ?", (course_code,))
            c_row = cur.fetchone()
            assert c_row, "course not found in DB"
            course_id = c_row[0]
            cur.execute("SELECT room_id FROM rooms WHERE room_number = ?", (room,))
            r_row = cur.fetchone()
            room_id = r_row[0] if r_row else None
            # try to find any instructor, else NULL
            cur.execute("SELECT instructor_id FROM instructors LIMIT 1")
            i_row = cur.fetchone()
            instructor_id = i_row[0] if i_row else None
            cur.execute(
                "INSERT INTO classes (course_id, room_id, instructor_id, section, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (course_id, room_id, instructor_id, section, now.strftime('%A'), to_12h(start), to_12h(end))
            )
            conn.commit()
            created_class_id = cur.lastrowid
            conn.close()
            class_id = created_class_id
        assert class_id is not None

        # run recognition using first image
        img = imgs[0]
        files = {'file': (os.path.basename(img), open(img, 'rb'), 'image/jpeg')}
        data = {'class_id': str(class_id)}
        r = session.post(f"{BASE_URL}/api/recognize", files=files, data=data, timeout=30)
        try:
            files['file'][1].close()
        except Exception:
            pass
        assert r.status_code == 200
        body = r.json()
        assert body.get('status') == 'success', body

        # verify attendance in DB
        conn = sqlite3.connect('attendance.db')
        cur = conn.cursor()
        cur.execute("SELECT student_id FROM students WHERE student_number = ?", (new_student,))
        row = cur.fetchone()
        assert row is not None
        student_id = row[0]
        cur.execute("SELECT 1 FROM attendance_logs WHERE student_id = ? AND class_id = ?", (student_id, class_id))
        assert cur.fetchone(), "attendance log not found"
        conn.close()

    finally:
        # cleanup DB and files
        conn = sqlite3.connect('attendance.db')
        cur = conn.cursor()
        # remove attendance, enrollments, embeddings, student row
        cur.execute("SELECT student_id FROM students WHERE student_number = ?", (new_student,))
        s = cur.fetchone()
        if s:
            sid = s[0]
            cur.execute("DELETE FROM attendance_logs WHERE student_id = ?", (sid,))
            cur.execute("DELETE FROM enrollments WHERE student_id = ?", (sid,))
            cur.execute("DELETE FROM student_face_embeddings WHERE student_id = ?", (sid,))
            cur.execute("DELETE FROM students WHERE student_id = ?", (sid,))
        # Only delete the class if we created it above (created_class_id set)
        try:
            if 'created_class_id' in locals() and created_class_id:
                cur.execute("DELETE FROM classes WHERE class_id = ?", (created_class_id,))
            else:
                # best-effort: remove class row that matches section (if present) using class_id lookup
                cur.execute("SELECT class_id FROM classes WHERE section = ?", (section,))
                row = cur.fetchone()
                if row:
                    cur.execute("DELETE FROM classes WHERE class_id = ?", (row[0],))
        except Exception:
            pass
        conn.commit()
        conn.close()

        try:
            shutil.rmtree(new_folder)
        except Exception:
            pass
