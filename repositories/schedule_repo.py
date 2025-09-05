
import sqlite3
from fastapi import Request, HTTPException
from models.schedule import ScheduleResponse

DB_PATH = "attendance.db"

class ScheduleRepository:
    async def get_room_schedule(self, room_code: str):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT course_code, section, instructor_name, day_of_week, start_time, end_time
                FROM classes WHERE room_id = ?
            """, (room_code,))
            schedule = [
                {
                    "courseCode": row[0],
                    "section": row[1],
                    "professor": row[2],
                    "day": row[3],
                    "startTime": row[4],
                    "endTime": row[5]
                }
                for row in cursor.fetchall()
            ]
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
            cursor.execute("DELETE FROM classes WHERE room_id = ?", (room_code,))

            # Insert room into rooms table if not exists, with floor_level and room_number
            # Always set or update floor_level and room_number for the room
            import re
            match = re.search(r"(\d+)$", room_code)
            if match:
                room_number = match.group(1)
                floor_level = int(room_number[0]) if len(room_number) > 0 else None
            else:
                room_number = None
                floor_level = None
            cursor.execute("SELECT 1 FROM rooms WHERE room_id = ?", (room_code,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO rooms (room_id, floor_level, room_number) VALUES (?, ?, ?)",
                    (room_code, floor_level, room_number)
                )
            else:
                cursor.execute(
                    "UPDATE rooms SET floor_level = ?, room_number = ? WHERE room_id = ?",
                    (floor_level, room_number, room_code)
                )

            for entry in merged:
                class_id = f"{entry.get('courseCode','')}_{entry.get('section','')}_{room_code}_{entry.get('day','')}"
                cursor.execute("""
                    INSERT INTO classes (class_id, course_code, section, room_id, instructor_name, day_of_week, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    class_id,
                    entry.get('courseCode',''),
                    entry.get('section',''),
                    room_code,
                    entry.get('professor',''),
                    entry.get('day',''),
                    entry.get('startTime',''),
                    entry.get('endTime','')
                ))
            conn.commit()
        return ScheduleResponse(schedule=merged)

    async def delete_room_schedule(self, room_code: str):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM classes WHERE room_id = ?", (room_code,))
            conn.commit()
        return {"detail": "Room schedule deleted"}

def get_schedule_repository():
    return ScheduleRepository()
