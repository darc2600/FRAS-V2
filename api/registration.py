from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from services.registration_service import RegistrationService, get_registration_service
from models.registration import RegistrationResponse
from typing import List

router = APIRouter()

@router.post("/api/registration", response_model=RegistrationResponse)
async def register_student(
    student_id: str = Form(...),
    name: str = Form(...),
    schedule: str = Form(...),  # JSON list of {course_code, section, room}
    images: List[UploadFile] = File(...),
    service: RegistrationService = Depends(get_registration_service)
):
    return await service.register_student(student_id, name, schedule, images)
