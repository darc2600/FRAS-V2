from repositories.room_repo import RoomRepository, get_room_repository
from fastapi import Depends
from typing import List, Dict

class RoomService:
    def __init__(self, repo: RoomRepository):
        self.repo = repo

    def get_rooms(self) -> List[str]:
        return self.repo.fetch_rooms()

    def get_courses(self, room: str) -> List[str]:
        return self.repo.fetch_courses(room)

    def get_sections(self, room: str, course: str) -> List[str]:
        return self.repo.fetch_sections(room, course)

    def get_floor_levels(self) -> List[int]:
        return self.repo.fetch_floor_levels()

    def get_rooms_by_floor(self, floor_level: int) -> List[Dict]:
        return self.repo.fetch_rooms_by_floor(floor_level)

    def get_courses_sections_by_room(self, room_id: int) -> List[Dict]:
        return self.repo.fetch_courses_sections_by_room(room_id)

def get_room_service(repo: RoomRepository = Depends(get_room_repository)):
    return RoomService(repo)
