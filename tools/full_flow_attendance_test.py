import requests
import json
import os
from glob import glob
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()
results = {}

# 0) choose a room
r = session.get(f"{BASE_URL}/api/rooms", timeout=5)
rooms = r.json() if r.status_code == 200 else []
if not rooms:
    print("No rooms available; aborting")
    raise SystemExit(1)
room_code = rooms[0]
results['room'] = room_code

# 1) choose a course from /api/courses
r = session.get(f"{BASE_URL}/api/courses", timeout=5)
courses = r.json() if r.status_code == 200 else []
if not courses:
    print("No courses available; aborting")
    raise SystemExit(1)
course_code = courses[0]['code']
results['course'] = course_code

# create a unique section name
timestamp = int(datetime.utcnow().timestamp())
section = f"TF{timestamp % 10000}"
results['section'] = section

# 2) create schedule entry for current day covering now
now = datetime.now()
day_name = now.strftime('%A')
start = now - timedelta(minutes=5)
end = now + timedelta(minutes=30)

def to_12h(dt):
    return dt.strftime('%I:%M%p')

schedule_entry = [{
    "courseCode": course_code,
    "section": section,
    "professor": "Brown, Michael",
    "day": day_name,
    "startTime": to_12h(start),
    "endTime": to_12h(end)
}]

# POST schedule to room
r = session.post(f"{BASE_URL}/api/room-schedule/{room_code}", json=schedule_entry, timeout=15)
results['create_schedule'] = {'status': r.status_code, 'text': r.text}

# 3) pick a student folder from dataset
dataset_dirs = [d for d in os.listdir('dataset') if os.path.isdir(os.path.join('dataset', d))]
# Prefer numeric folder names
student_folder = None
for d in dataset_dirs:
    if d.isdigit():
        student_folder = d
        break
if not student_folder and dataset_dirs:
    student_folder = dataset_dirs[0]

if not student_folder:
    print('No student folders found under dataset; aborting')
    raise SystemExit(1)

results['student_folder'] = student_folder

# images to upload
image_files = glob(os.path.join('dataset', student_folder, '*.jpg'))
if not image_files:
    print('No images in student folder; aborting')
    raise SystemExit(1)

# 4) register student via /api/registration with schedule pointing to our created course/section
student_number = student_folder
last_name = 'Auto'
first_name = student_folder
email = f'{student_number}@example.local'
created_at = datetime.utcnow().isoformat()

# build schedule param as JSON string
schedule_param = json.dumps([{"course_code": course_code, "section": section}])

files = []
for img in image_files[:3]:  # send up to 3 images
    files.append(('images', (os.path.basename(img), open(img, 'rb'), 'image/jpeg')))

data = {
    'student_number': student_number,
    'last_name': last_name,
    'first_name': first_name,
    'email': email,
    'created_at': created_at,
    'schedule': schedule_param
}

r = session.post(f"{BASE_URL}/api/registration", data=data, files=files, timeout=30)
results['registration'] = {'status': r.status_code, 'text': r.text}

# close file handles
for _, f in files:
    try:
        f[1].close()
    except Exception:
        pass

# 5) find class_id matching course_code and section
r = session.get(f"{BASE_URL}/api/classes", timeout=5)
classes = r.json() if r.status_code == 200 else []
class_id = None
for c in classes:
    if c.get('course_code') == course_code and c.get('section') == section:
        class_id = c.get('id')
        break
results['class_id'] = class_id

# 6) call /api/recognize with one image
if class_id:
    img = image_files[0]
    files = {'file': (os.path.basename(img), open(img, 'rb'), 'image/jpeg')}
    data = {'class_id': str(class_id)}
    r = session.post(f"{BASE_URL}/api/recognize", files=files, data=data, timeout=30)
    try:
        body = r.json()
    except Exception:
        body = r.text
    results['recognize'] = {'status': r.status_code, 'body': body}
    try:
        files['file'][1].close()
    except Exception:
        pass
else:
    results['recognize'] = {'skipped': 'no class_id'}

# 7) fetch attendance for course/section
r = session.get(f"{BASE_URL}/api/attendance", params={'course_code': course_code, 'section': section}, timeout=10)
try:
    att = r.json()
except Exception:
    att = r.text
results['attendance'] = {'status': r.status_code, 'body': att}

# write results
with open('tools/full_flow_attendance_test_results.json', 'w', encoding='utf-8') as fh:
    json.dump(results, fh, indent=2)

print(json.dumps(results, indent=2))
print('Wrote tools/full_flow_attendance_test_results.json')
