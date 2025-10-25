from fastapi import APIRouter, UploadFile, File, Form, Depends
from services.recognition_service import RecognitionService, get_recognition_service
from models.recognition import RecognitionResponse

router = APIRouter()

@router.post("/api/recognize", response_model=RecognitionResponse)
async def recognize_face(
    file: UploadFile = File(...),
    class_id: int = Form(...),
    service: RecognitionService = Depends(get_recognition_service)
):
    return await service.recognize_face(file, class_id)
