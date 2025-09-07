from repositories.recognition_repo import RecognitionRepository, get_recognition_repository
from models.recognition import RecognitionResponse
from fastapi import UploadFile, Depends

class RecognitionService:
    def __init__(self, repo: RecognitionRepository):
        self.repo = repo

    async def recognize_face(self, file: UploadFile, course_code: str, section: str, room: str) -> RecognitionResponse:
        return await self.repo.recognize_face(file, course_code, section, room)

def get_recognition_service(repo: RecognitionRepository = Depends(get_recognition_repository)):
    return RecognitionService(repo)
