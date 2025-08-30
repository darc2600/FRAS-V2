import os
import json
from fastapi import Request, HTTPException
from models.schedule import ScheduleResponse

class ScheduleRepository:
    async def get_room_schedule(self, room_code: str) -> ScheduleResponse:
        schedule_path = os.path.join("schedules", f"{room_code}.json")
        if not os.path.exists(schedule_path):
            raise HTTPException(status_code=404, detail="Room schedule not found")
        with open(schedule_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ScheduleResponse(schedule=data)

    async def update_room_schedule(self, room_code: str, request: Request) -> ScheduleResponse:
        os.makedirs("schedules", exist_ok=True)
        schedule_path = os.path.join("schedules", f"{room_code}.json")
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            schedule = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            schedule_str = form.get("schedule")
            if not schedule_str:
                raise HTTPException(status_code=400, detail="Missing 'schedule' field in form data.")
            try:
                schedule = json.loads(schedule_str)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON in 'schedule' field.")
        else:
            raise HTTPException(status_code=415, detail="Unsupported Media Type")
        with open(schedule_path, "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
        return ScheduleResponse(schedule=schedule)

def get_schedule_repository():
    return ScheduleRepository()
