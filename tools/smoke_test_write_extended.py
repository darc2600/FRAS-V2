import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()
results = {}

# obtain token
creds = [("test.superadmin@fras.com", "password123"), ("superadmin@fras.com", "super123")]
for email, pwd in creds:
    try:
        r = session.post(f"{BASE_URL}/api/login", json={"email": email, "password": pwd}, timeout=5)
        if r.status_code in (200,201):
            token = None
            try:
                token = r.json().get("access_token")
            except Exception:
                pass
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
                results['login'] = {"email": email, "status": r.status_code}
                break
            else:
                results['login'] = {"email": email, "status": r.status_code, "note": "no token"}
    except Exception as e:
        results['login'] = {"email": email, "error": str(e)}

if 'login' not in results:
    print(json.dumps({"error": "no login token obtained"}))
    raise SystemExit(1)

# 1) Create support ticket
ticket_payload = {
    "subject": f"Smoke test ticket {int(time.time())}",
    "description": "This is an automated smoke test ticket. Please ignore.",
    "category": "other",
    "priority": "low"
}
try:
    r = session.post(f"{BASE_URL}/api/support/tickets", json=ticket_payload, timeout=10)
    results['create_ticket'] = {"status": r.status_code, "text": r.text}
    ticket_id = None
    if r.status_code in (200,201):
        try:
            ticket_id = r.json().get('ticket_id')
        except Exception:
            pass
    if not ticket_id:
        print("Could not obtain ticket_id; aborting ticket flow")
    else:
        # Admin update ticket status to resolved
        r2 = session.put(f"{BASE_URL}/api/admin/support/tickets/{ticket_id}", json={"status": "resolved"}, timeout=10)
        results['update_ticket'] = {"status": r2.status_code, "text": r2.text}
        # Add a public reply
        r3 = session.post(f"{BASE_URL}/api/admin/support/tickets/{ticket_id}/replies", json={"message": "Automated reply (public)", "is_internal": False}, timeout=10)
        results['reply_ticket'] = {"status": r3.status_code, "text": r3.text}
except Exception as e:
    results['create_ticket'] = {"error": str(e)}

# 2) Create room schedule
# Fetch a room, a course, and an instructor
try:
    r_rooms = session.get(f"{BASE_URL}/api/rooms", timeout=5)
    rooms = r_rooms.json() if r_rooms.status_code == 200 else []
    room_code = rooms[0] if rooms else None

    r_courses = session.get(f"{BASE_URL}/api/courses", timeout=5)
    courses = r_courses.json() if r_courses.status_code == 200 else []
    course_code = courses[0]['code'] if courses else None

    r_instructors = session.get(f"{BASE_URL}/api/instructors", timeout=5)
    instructors = r_instructors.json() if r_instructors.status_code == 200 else []
    # Filter out invalid entries like 'None, None' or empty strings
    instructor = None
    for inst in instructors:
        try:
            if isinstance(inst, str) and inst.strip() and 'None' not in inst:
                instructor = inst
                break
        except Exception:
            continue

    results['room_sample'] = {'room': room_code, 'course': course_code, 'instructor': instructor}

    if room_code and course_code and instructor:
        # Build a minimal schedule entry
        schedule_entry = [
            {
                "courseCode": course_code,
                "section": "SMK",
                "professor": instructor,  # expects 'Last, First'
                "day": "Monday",
                "startTime": "07:00AM",
                "endTime": "08:10AM"
            }
        ]
        # POST schedule as JSON
        r4 = session.post(f"{BASE_URL}/api/room-schedule/{room_code}", json=schedule_entry, timeout=15)
        results['create_schedule'] = {"status": r4.status_code, "text": r4.text}
        # DELETE schedule to clean up
        r5 = session.delete(f"{BASE_URL}/api/room-schedule/{room_code}", timeout=15)
        results['delete_schedule'] = {"status": r5.status_code, "text": r5.text}
    else:
        results['create_schedule'] = {"skipped": "missing sample room/course/instructor"}

except Exception as e:
    results['create_schedule'] = {"error": str(e)}

with open('tools/smoke_test_write_extended_results.json', 'w', encoding='utf-8') as fh:
    json.dump(results, fh, indent=2)

print(json.dumps(results, indent=2))
print('Wrote tools/smoke_test_write_extended_results.json')
