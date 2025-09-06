from fastapi import APIRouter, Query, Depends
from services.room_service import RoomService, get_room_service
from typing import List

router = APIRouter()

@router.get("/api/rooms", response_model=List[str])
def get_rooms(service: RoomService = Depends(get_room_service)):
    return service.get_rooms()

@router.get("/api/courses", response_model=List[str])
def get_courses(room: str = Query(...), service: RoomService = Depends(get_room_service)):
    return service.get_courses(room)

@router.get("/api/sections", response_model=List[str])
def get_sections(room: str = Query(...), course: str = Query(...), service: RoomService = Depends(get_room_service)):
    return service.get_sections(room, course)
