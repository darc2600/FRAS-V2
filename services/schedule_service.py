from repositories.schedule_repo import ScheduleRepository, get_schedule_repository
from models.schedule import ScheduleResponse
from fastapi import Request, Depends

class ScheduleService:
    def __init__(self, repo: ScheduleRepository):
        self.repo = repo

    async def get_room_schedule(self, room_code: str):
        schedule = self.repo.get_room_schedule(room_code)
        return {"schedule": schedule}

    async def update_room_schedule(self, room_code: str, request: Request) -> ScheduleResponse:
        return await self.repo.update_room_schedule(room_code, request)

    async def delete_room_schedule(self, room_code: str):
        return await self.repo.delete_room_schedule(room_code)

def get_schedule_service(repo: ScheduleRepository = Depends(get_schedule_repository)):
    return ScheduleService(repo)
