from repositories.schedule_repo import ScheduleRepository, get_schedule_repository
from models.schedule import ScheduleResponse
from fastapi import Request, Depends

class ScheduleService:
    def __init__(self, repo: ScheduleRepository):
        self.repo = repo

    async def get_room_schedule(self, room_code: str) -> ScheduleResponse:
        return await self.repo.get_room_schedule(room_code)

    async def update_room_schedule(self, room_code: str, request: Request) -> ScheduleResponse:
        return await self.repo.update_room_schedule(room_code, request)

def get_schedule_service(repo: ScheduleRepository = Depends(get_schedule_repository)):
    return ScheduleService(repo)
