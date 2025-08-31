from fastapi import APIRouter
import os
import re

router = APIRouter()

def normalize_room_code(room: str) -> str:
    # Extract digits from room code (e.g., MPO305 -> 305)
    match = re.search(r"(\d{3,})", room)
    return match.group(1) if match else room

def get_floor_from_room(room: str) -> int:
    norm = normalize_room_code(room)
    if len(norm) >= 3 and norm.isdigit():
        return int(norm[0])  # 305 -> 3rd floor
    return 0

@router.get("/api/rooms/floors")
def get_rooms_with_floors():
    schedules_dir = "schedules"
    if not os.path.exists(schedules_dir):
        return []
    rooms = [f[:-5] for f in os.listdir(schedules_dir) if f.endswith(".json")]
    result = []
    for room in rooms:
        norm = normalize_room_code(room)
        floor = get_floor_from_room(room)
        result.append({
            "room": room,
            "normalized": norm,
            "floor": floor
        })
    return result
