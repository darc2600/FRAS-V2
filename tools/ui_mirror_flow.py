"""UI-mirroring script: exercises frontend-like payloads for registration, capture, and recognize.
Usage: python tools/ui_mirror_flow.py
Requires a running server at BASE_URL and an existing dataset source folder to copy images from.
"""
import requests
import json
import os
import shutil
from glob import glob
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()

def choose_first_room_and_course():
    r = session.get(f"{BASE_URL}/api/rooms", timeout=5)
    rooms = r.json() if r.status_code == 200 else []
    r2 = session.get(f"{BASE_URL}/api/courses", timeout=5)
    courses = r2.json() if r2.status_code == 200 else []
    return (rooms[0] if rooms else None, courses[0] if courses else None)

def create_schedule(room_code, course_code, section, day_name, start_dt, end_dt):
    def to_12h(dt):
        return dt.strftime('%I:%M%p')
    entry = [{
        "courseCode": course_code,
        "section": section,
        "professor": "Brown, Michael",
        "day": day_name,
        "startTime": to_12h(start_dt),
        "endTime": to_12h(end_dt)
    }]
    r = session.post(f"{BASE_URL}/api/room-schedule/{room_code}", json=entry, timeout=15)
    return r

def register_student_from_folder(student_number, last_name, first_name, email, src_folder):
    # use up to 3 images from src_folder and send to /api/registration
    image_files = glob(os.path.join(src_folder, '*.jpg'))
    if not image_files:
        raise RuntimeError("No images in source folder")
    files = []
    for img in image_files[:3]:
        files.append(('images', (os.path.basename(img), open(img, 'rb'), 'image/jpeg')))

    data = {
        'student_number': student_number,
        'last_name': last_name,
        'first_name': first_name,
        'email': email,
        'created_at': datetime.utcnow().isoformat(),
        'schedule': json.dumps([]),
    }
    r = session.post(f"{BASE_URL}/api/registration", data=data, files=files, timeout=30)

    for _, f in files:
        try:
            f[1].close()
        except Exception:
            pass
    return r

def capture_snapshot_for_student(student_number, image_path):
    # frontend may POST to /api/capture with student_number + file
    files = {'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')}
    data = {'student_number': student_number}
    try:
        r = session.post(f"{BASE_URL}/api/capture", files=files, data=data, timeout=30)
    except Exception:
        r = None
    try:
        files['file'][1].close()
    except Exception:
        pass
    return r

def recognize_for_class(class_id, image_path):
    files = {'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')}
    data = {'class_id': str(class_id)}
    r = session.post(f"{BASE_URL}/api/recognize", files=files, data=data, timeout=30)
    try:
        files['file'][1].close()
    except Exception:
        pass
    return r

def main():
    room, course = choose_first_room_and_course()
    if not room or not course:
        print('No room or course available')
        return

    now = datetime.now()
    start = now - timedelta(minutes=5)
    end = now + timedelta(minutes=30)
    day_name = now.strftime('%A')

    section = f"UI{int(datetime.utcnow().timestamp())%10000}"
    print('Creating schedule...')
    r = create_schedule(room, course['code'], section, day_name, start, end)
    print('Schedule response:', r.status_code, r.text)

    # choose a source folder
    dataset_dirs = [d for d in os.listdir('dataset') if os.path.isdir(os.path.join('dataset', d))]
    if not dataset_dirs:
        print('No dataset folders')
        return
    src = dataset_dirs[0]
    new_student = f"ui{int(datetime.utcnow().timestamp())}"

    # copy images locally into a temp folder so frontend-like registration can reuse them
    src_folder = os.path.join('dataset', src)
    tmp_folder = os.path.join('dataset', new_student)
    os.makedirs(tmp_folder, exist_ok=True)
    for i, img in enumerate(glob(os.path.join(src_folder, '*.jpg'))[:3], start=1):
        shutil.copy(img, os.path.join(tmp_folder, f'capture_{i}.jpg'))

    print('Registering student...')
    r = register_student_from_folder(new_student, 'UIAuto', 'UIAuto', f'{new_student}@example.local', tmp_folder)
    print('Registration:', r.status_code, r.text)

    # find class id
    r = session.get(f"{BASE_URL}/api/classes", timeout=5)
    classes = r.json() if r.status_code == 200 else []
    class_id = None
    for c in classes:
        if c.get('course_code') == course['code'] and c.get('section') == section:
            class_id = c.get('id')
            break

    if not class_id:
        print('Could not find class id')
        return

    # capture then recognize
    image_path = glob(os.path.join(tmp_folder, '*.jpg'))[0]
    print('Attempting capture (optional endpoint)...')
    cap = capture_snapshot_for_student(new_student, image_path)
    print('Capture response:', cap.status_code if cap else 'N/A')

    print('Recognizing...')
    rec = recognize_for_class(class_id, image_path)
    print('Recognize response:', rec.status_code, rec.text)

if __name__ == '__main__':
    main()
