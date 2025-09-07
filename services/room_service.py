from repositories.room_repo import RoomRepository, get_room_repository
from fastapi import Depends
from typing import List

class RoomService:
    def __init__(self, repo: RoomRepository):
        self.repo = repo

    def get_rooms(self) -> List[str]:
        return self.repo.fetch_rooms()

    def get_courses(self, room: str) -> List[str]:
        return self.repo.fetch_courses(room)

    def get_sections(self, room: str, course: str) -> List[str]:
        return self.repo.fetch_sections(room, course)

def get_room_service(repo: RoomRepository = Depends(get_room_repository)):
    return RoomService(repo)
