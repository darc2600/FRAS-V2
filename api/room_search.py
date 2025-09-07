from fastapi import APIRouter, Query
import os
import json
from typing import List, Dict

router = APIRouter()

@router.get("/api/rooms/search", tags=["Rooms"])
def search_rooms(query: str = Query(...)) -> List[str]:
    """
    Search for rooms by partial/case-insensitive match.
    """
    schedules_dir = "schedules"
    if not os.path.exists(schedules_dir):
        return []
    query_lower = query.lower()
    rooms = [f[:-5] for f in os.listdir(schedules_dir) if f.endswith(".json")]
    return [room for room in rooms if query_lower in room.lower()]

@router.get("/api/course-sections", tags=["Courses", "Sections"])
def get_course_sections(room: str = Query(...)) -> List[str]:
    """
    Return all unique course-section pairs for a given room as 'COURSE_CODE - SECTION'.
    """
    schedule_path = os.path.join("schedules", f"{room}.json")
    if not os.path.exists(schedule_path):
        return []
    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    pairs = set()
    for entry in schedule:
        course = entry.get("courseCode")
        section = entry.get("section")
        if course and section:
            pairs.add(f"{course} - {section}")
    return sorted(list(pairs))
