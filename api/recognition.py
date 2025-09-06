from fastapi import APIRouter, UploadFile, File, Form, Depends
from services.recognition_service import RecognitionService, get_recognition_service
from models.recognition import RecognitionResponse

router = APIRouter()

@router.post("/api/recognize", response_model=RecognitionResponse)
async def recognize_face(
    file: UploadFile = File(...),
    course_code: str = Form(...),
    section: str = Form(...),
    room: str = Form(...),
    service: RecognitionService = Depends(get_recognition_service)
):
    return await service.recognize_face(file, course_code, section, room)
