from repositories.recognition_repo import RecognitionRepository, get_recognition_repository
from models.recognition import RecognitionResponse
from fastapi import UploadFile, Depends

class RecognitionService:
    def __init__(self, repo: RecognitionRepository):
        self.repo = repo

    async def recognize_face(self, file: UploadFile, class_id: int) -> RecognitionResponse:
        return await self.repo.recognize_face(file, class_id)

    async def mark_absents(self, class_id: int, date: str):
        return await self.repo.mark_absents(class_id, date)

def get_recognition_service(repo: RecognitionRepository = Depends(get_recognition_repository)):
    return RecognitionService(repo)
