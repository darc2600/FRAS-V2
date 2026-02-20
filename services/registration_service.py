from repositories.registration_repo import RegistrationRepository, get_registration_repository
from models.registration import RegistrationResponse
from fastapi import UploadFile, HTTPException, Depends
from typing import List
import json

class RegistrationService:
    def __init__(self, repo: RegistrationRepository):
        self.repo = repo

    async def register_student(
        self,
        student_number: str,
        last_name: str,
        first_name: str,
        email: str,
        created_at: str,
        schedule: str,
        images: List[UploadFile]
    ) -> RegistrationResponse:
        try:
            schedule_entries = json.loads(schedule)
            print(f"[DEBUG] Parsed schedule_entries: {schedule_entries}")
            print(f"[DEBUG] Number of schedule_entries: {len(schedule_entries)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid schedule: {e}")
        return await self.repo.register_student(
            student_number,
            last_name,
            first_name,
            email,
            created_at,
            schedule_entries,
            images
        )

def get_registration_service(repo: RegistrationRepository = Depends(get_registration_repository)):
    return RegistrationService(repo)
