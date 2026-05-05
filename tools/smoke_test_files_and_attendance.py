import requests
import json
import os
from glob import glob
from time import time

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()
results = {}

# helper to pick an image from dataset
def pick_sample_image():
    candidates = glob('dataset/**/capture_1.jpg', recursive=True)
    if not candidates:
        # fallback any image
        candidates = glob('**/*.jpg', recursive=True)
    return candidates[0] if candidates else None

img_path = pick_sample_image()
results['sample_image'] = img_path

# 1) Registration (multipart/form-data with one image)
if img_path:
    data = {
        'student_number': f'TEST{int(time())}',
        'last_name': 'Smoke',
        'first_name': 'Test',
        'email': f'smoke.test.{int(time())}@example.local',
        'created_at': '2026-05-04T10:00:00',
        'schedule': '[]'
    }
    files = [('images', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg'))]
    try:
        r = session.post(f"{BASE_URL}/api/registration", data=data, files=files, timeout=20)
        results['registration'] = {'status': r.status_code, 'text': r.text}
    except Exception as e:
        results['registration'] = {'error': str(e)}
else:
    results['registration'] = {'skipped': 'no sample image found'}

# 2) Capture: pick a student id from /api/students and course/section
try:
    r_students = session.get(f"{BASE_URL}/api/students", timeout=5)
    students = r_students.json() if r_students.status_code == 200 else []
    student_id = students[0]['id'] if students else None

    r_courses = session.get(f"{BASE_URL}/api/courses", timeout=5)
    courses = r_courses.json() if r_courses.status_code == 200 else []
    course_code = courses[0]['code'] if courses else None

    # if we have course_code, fetch sections
    section = None
    if course_code:
        r_sections = session.get(f"{BASE_URL}/api/courses/{course_code}/sections", timeout=5)
        secs = r_sections.json() if r_sections.status_code == 200 else []
        section = secs[0] if secs else None

    results['capture_sample'] = {'student_id': student_id, 'course_code': course_code, 'section': section}

    if img_path and student_id and course_code and section:
        files = {'file': (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')}
        data = {'course_code': course_code, 'section': section, 'student_id': str(student_id)}
        r = session.post(f"{BASE_URL}/api/capture", files=files, data=data, timeout=15)
        results['capture'] = {'status': r.status_code, 'text': r.text}
    else:
        results['capture'] = {'skipped': 'missing student/course/section or image'}
except Exception as e:
    results['capture'] = {'error': str(e)}

# 3) Recognize: need class_id and file
try:
    r_classes = session.get(f"{BASE_URL}/api/classes", timeout=5)
    classes = r_classes.json() if r_classes.status_code == 200 else []
    class_id = classes[0]['id'] if classes else None
    results['recognize_sample'] = {'class_id': class_id}
    if img_path and class_id:
        files = {'file': (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')}
        data = {'class_id': str(class_id)}
        r = session.post(f"{BASE_URL}/api/recognize", files=files, data=data, timeout=20)
        # recognition may return complex JSON
        try:
            body = r.json()
        except Exception:
            body = r.text[:400]
        results['recognize'] = {'status': r.status_code, 'body': body}
    else:
        results['recognize'] = {'skipped': 'missing class_id or image'}
except Exception as e:
    results['recognize'] = {'error': str(e)}

# 4) Attendance: pick a course_code and section (reuse earlier) and call /api/attendance
try:
    if not course_code:
        r_courses = session.get(f"{BASE_URL}/api/courses", timeout=5)
        courses = r_courses.json() if r_courses.status_code == 200 else []
        course_code = courses[0]['code'] if courses else None
    if course_code:
        r_sections = session.get(f"{BASE_URL}/api/courses/{course_code}/sections", timeout=5)
        secs = r_sections.json() if r_sections.status_code == 200 else []
        section = secs[0] if secs else None
    if course_code and section:
        r = session.get(f"{BASE_URL}/api/attendance", params={'course_code': course_code, 'section': section}, timeout=10)
        try:
            body = r.json()
        except Exception:
            body = r.text[:400]
        results['attendance'] = {'status': r.status_code, 'body': body}
    else:
        results['attendance'] = {'skipped': 'no course/section available'}
except Exception as e:
    results['attendance'] = {'error': str(e)}

# Write results
with open('tools/smoke_test_files_and_attendance_results.json', 'w', encoding='utf-8') as fh:
    json.dump(results, fh, indent=2)

print(json.dumps(results, indent=2))
print('Wrote tools/smoke_test_files_and_attendance_results.json')
