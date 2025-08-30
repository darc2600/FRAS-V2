from fastapi import APIRouter, Request, Depends
from services.schedule_service import ScheduleService, get_schedule_service
from models.schedule import ScheduleResponse

router = APIRouter()

@router.get("/api/room-schedule/{room_code}", response_model=ScheduleResponse)
async def get_room_schedule(room_code: str, service: ScheduleService = Depends(get_schedule_service)):
    return await service.get_room_schedule(room_code)

@router.post("/api/room-schedule/{room_code}", response_model=ScheduleResponse)
async def update_room_schedule(room_code: str, request: Request, service: ScheduleService = Depends(get_schedule_service)):
    return await service.update_room_schedule(room_code, request)
