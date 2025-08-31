from fastapi import APIRouter, Request, Depends, HTTPException, Response
from services.schedule_service import ScheduleService, get_schedule_service
from models.schedule import ScheduleResponse
from typing import List

router = APIRouter()

@router.get("/api/room-schedule/{room_code}", response_model=ScheduleResponse)
async def get_room_schedule(room_code: str, service: ScheduleService = Depends(get_schedule_service)):
    schedule = await service.get_room_schedule(room_code)
    # Always wrap in ScheduleResponse with a list
    return ScheduleResponse(schedule=schedule)

@router.post("/api/room-schedule/{room_code}", response_model=ScheduleResponse)
async def update_room_schedule(room_code: str, request: Request, service: ScheduleService = Depends(get_schedule_service)):
    return await service.update_room_schedule(room_code, request)

# Delete a room schedule file using the service layer
@router.delete("/api/room-schedule/{room_code}")
async def delete_room_schedule(room_code: str, service: ScheduleService = Depends(get_schedule_service)):
    return await service.delete_room_schedule(room_code)
