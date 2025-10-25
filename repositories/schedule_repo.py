
import sqlite3
from fastapi import Request, HTTPException
from models.schedule import ScheduleResponse

DB_PATH = "attendance.db"

class ScheduleRepository:
    async def get_room_schedule(self, room_code: str):
        TIME_SLOTS = [
            "07:00AM - 08:10AM", "08:10AM - 09:20AM", "09:20AM - 10:30AM", "10:30AM - 11:40AM",
            "11:40AM - 12:50PM", "12:50PM - 02:00PM", "02:00PM - 03:10PM", "03:10PM - 04:20PM",
            "04:20PM - 05:30PM", "05:30PM - 06:40PM", "06:40PM - 07:50PM", "07:50PM - 09:00PM"
        ]
        DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        def convert_to_12_hour(time_24h):
            """Convert 24-hour time (HH:MM) to 12-hour format (HH:MMAM/PM)"""
            hour, minute = map(int, time_24h.split(':'))
            if hour == 0:
                return f"12:{minute:02d}AM"
            elif hour < 12:
                return f"{hour:02d}:{minute:02d}AM"
            elif hour == 12:
                return f"12:{minute:02d}PM"
            else:
                return f"{hour-12:02d}:{minute:02d}PM"
        
        def time_to_minutes(t):
            import re
            match = re.match(r"(\d{1,2}):(\d{2})(AM|PM)", t)
            if not match:
                return None
            hour, minute, ampm = int(match.group(1)), int(match.group(2)), match.group(3)
            if ampm == "PM" and hour != 12:
                hour += 12
            if ampm == "AM" and hour == 12:
                hour = 0
            return hour * 60 + minute
        
        def slot_range(start_24h, end_24h):
            start_12h = convert_to_12_hour(start_24h)
            end_12h = convert_to_12_hour(end_24h)
            slots = []
            in_range = False
            for slot in TIME_SLOTS:
                slot_start, slot_end = slot.split(' - ')
                if slot_start == start_12h:
                    in_range = True
                if in_range:
                    slots.append(slot)
                if slot_end == end_12h:
                    break
            return slots
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT room_id FROM rooms WHERE room_number = ?", (room_code,))
            row = cursor.fetchone()
            if not row:
                return []
            room_id = row[0]
            cursor.execute("""
                SELECT co.course_code, c.section, i.last_name || ', ' || i.first_name as professor, c.day_of_week, c.start_time, c.end_time, c.instructor_id
                FROM classes c
                LEFT JOIN courses co ON c.course_id = co.course_id
                LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
                WHERE c.room_id = ?
            """, (room_id,))
            schedule = []
            for row in cursor.fetchall():
                courseCode, section, professor, day, startTime, endTime, instructorId = row
                for slot in slot_range(startTime, endTime):
                    slot_start, slot_end = slot.split(' - ')
                    schedule.append({
                        "courseCode": courseCode,
                        "section": section,
                        "professor": professor,
                        "day": day,
                        "startTime": slot_start,
                        "endTime": slot_end,
                        "instructorId": instructorId
                    })
        return schedule

    async def update_room_schedule(self, room_code: str, request: Request) -> ScheduleResponse:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            schedule = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            schedule_str = form.get("schedule")
            if not schedule_str:
                raise HTTPException(status_code=400, detail="Missing 'schedule' field in form data.")
            try:
                import json
                schedule = json.loads(schedule_str)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON in 'schedule' field.")
        else:
            raise HTTPException(status_code=415, detail="Unsupported Media Type")

        # Merge consecutive slots for the same class
        def time_to_minutes(t):
            import re
            match = re.match(r"(\d{1,2}):(\d{2})(AM|PM)", t)
            if not match:
                return None
            hour, minute, ampm = int(match.group(1)), int(match.group(2)), match.group(3)
            if ampm == "PM" and hour != 12:
                hour += 12
            if ampm == "AM" and hour == 12:
                hour = 0
            return hour * 60 + minute

        def minutes_to_time(m):
            hour = m // 60
            minute = m % 60
            ampm = "AM" if hour < 12 else "PM"
            hour12 = hour if 1 <= hour <= 12 else (hour - 12 if hour > 12 else 12)
            return f"{hour12:02d}:{minute:02d}{ampm}"

        # Sort and group schedule entries
        schedule_sorted = sorted(schedule, key=lambda x: (
            x.get('courseCode',''), x.get('section',''), x.get('professor',''), x.get('day',''), time_to_minutes(x.get('startTime','00:00AM'))
        ))
        merged = []
        for entry in schedule_sorted:
            if not merged:
                merged.append(entry.copy())
                continue
            last = merged[-1]
            # Check if this entry is consecutive with the last
            same_class = (
                last.get('courseCode','') == entry.get('courseCode','') and
                last.get('section','') == entry.get('section','') and
                last.get('professor','') == entry.get('professor','') and
                last.get('day','') == entry.get('day','')
            )
            last_end = time_to_minutes(last.get('endTime',''))
            this_start = time_to_minutes(entry.get('startTime',''))
            # If consecutive (last end == this start), merge
            if same_class and last_end == this_start:
                # Extend the last's end time
                merged[-1]['endTime'] = entry.get('endTime','')
            else:
                merged.append(entry.copy())

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Get or create room
            import re
            match = re.search(r"(\d+)$", room_code)
            if match:
                room_number = match.group(1)
                floor_level = int(room_number[0]) if len(room_number) > 0 else None
            else:
                room_number = None
                floor_level = None
            cursor.execute("SELECT room_id FROM rooms WHERE room_number = ?", (room_code,))
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "INSERT INTO rooms (floor_level, room_number, campus_id, building_id) VALUES (?, ?, 1, 1)",
                    (floor_level, room_number)
                )
                room_id = cursor.lastrowid
            else:
                room_id = row[0]
                cursor.execute(
                    "UPDATE rooms SET floor_level = ?, room_number = ?, campus_id = 1, building_id = 1 WHERE room_id = ?",
                    (floor_level, room_number, room_id)
                )
            cursor.execute("DELETE FROM classes WHERE room_id = ?", (room_id,))

            for entry in merged:
                course_code = entry.get('courseCode','')
                # Get course_id from course_code
                cursor.execute('SELECT course_id FROM courses WHERE course_code = ?', (course_code,))
                course_row = cursor.fetchone()
                if not course_row:
                    continue  # Skip if course not found
                course_id = course_row[0]
                class_id = f"{course_code}_{entry.get('section','')}_{room_code}_{entry.get('day','')}"
                instructor_id = entry.get('instructorId') or None
                cursor.execute("""
                    INSERT INTO classes (class_id, course_id, section, room_id, instructor_id, day_of_week, start_time, end_time, term_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    class_id,
                    course_id,
                    entry.get('section',''),
                    room_id,
                    instructor_id,
                    entry.get('day',''),
                    entry.get('startTime',''),
                    entry.get('endTime',''),
                    None  # term_id
                ))
            conn.commit()
        return ScheduleResponse(schedule=merged)

    async def delete_room_schedule(self, room_code: str):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM classes WHERE room_id IN (SELECT room_id FROM rooms WHERE room_number = ?)", (room_code,))
            conn.commit()
        return {"detail": "Room schedule deleted"}

def get_schedule_repository():
    return ScheduleRepository()
