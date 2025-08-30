from fastapi import APIRouter, UploadFile, File, Form, Depends
from services.capture_service import CaptureService, get_capture_service
from models.capture import CaptureResponse

router = APIRouter()

@router.post("/api/capture", response_model=CaptureResponse)
async def capture_image(
    file: UploadFile = File(...),
    course_code: str = Form(...),
    section: str = Form(...),
    student_id: str = Form(...),
    service: CaptureService = Depends(get_capture_service)
):
    return await service.capture_image(file, course_code, section, student_id)
