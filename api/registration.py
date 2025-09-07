from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from services.registration_service import RegistrationService, get_registration_service
from models.registration import RegistrationResponse
from typing import List

router = APIRouter()


@router.post("/api/registration", response_model=RegistrationResponse)
async def register_student(
    student_number: str = Form(...),
    last_name: str = Form(...),
    first_name: str = Form(...),
    email: str = Form(...),
    created_at: str = Form(...),
    schedule: str = Form(...),  # JSON list of {course_code, section, room}
    images: List[UploadFile] = File(...),
    service: RegistrationService = Depends(get_registration_service)
):
    return await service.register_student(
        student_number=student_number,
        last_name=last_name,
        first_name=first_name,
        email=email,
        created_at=created_at,
        schedule=schedule,
        images=images
    )
