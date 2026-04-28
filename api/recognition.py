from fastapi import APIRouter, UploadFile, File, Form, Depends
import logging
from services.recognition_service import RecognitionService, get_recognition_service
from models.recognition import RecognitionResponse

router = APIRouter()

@router.post("/api/recognize", response_model=RecognitionResponse)
async def recognize_face(
    file: UploadFile = File(...),
    class_id: int = Form(...),
    service: RecognitionService = Depends(get_recognition_service)
):
    LOG = logging.getLogger(__name__)
    try:
        return await service.recognize_face(file, class_id)
    except Exception as e:
        LOG.exception("Unhandled exception in /api/recognize")
        # Return a structured RecognitionResponse so frontend gets JSON
        return RecognitionResponse(status="error", message="Internal server error")

@router.post("/api/mark-absents")
async def mark_absents(
    class_id: int = Form(...),
    date: str = Form(...),  # YYYY-MM-DD
    service: RecognitionService = Depends(get_recognition_service)
):
    return await service.mark_absents(class_id, date)
