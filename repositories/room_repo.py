import os
import json
from typing import List

class RoomRepository:
    def fetch_rooms(self) -> List[str]:
        schedules_dir = "schedules"
        if not os.path.exists(schedules_dir):
            return []
        return [f[:-5] for f in os.listdir(schedules_dir) if f.endswith(".json")]

    def fetch_courses(self, room: str) -> List[str]:
        schedule_path = os.path.join("schedules", f"{room}.json")
        if not os.path.exists(schedule_path):
            return []
        with open(schedule_path, "r", encoding="utf-8") as f:
            schedule = json.load(f)
        return sorted(list(set(entry.get("courseCode") for entry in schedule if entry.get("courseCode"))))

    def fetch_sections(self, room: str, course: str) -> List[str]:
        schedule_path = os.path.join("schedules", f"{room}.json")
        if not os.path.exists(schedule_path):
            return []
        with open(schedule_path, "r", encoding="utf-8") as f:
            schedule = json.load(f)
        return sorted(list(set(entry.get("section") for entry in schedule if entry.get("courseCode") == course and entry.get("section"))))

def get_room_repository():
    return RoomRepository()
