from repositories.capture_repo import CaptureRepository, get_capture_repository
from models.capture import CaptureResponse
from fastapi import UploadFile, Depends

class CaptureService:
    def __init__(self, repo: CaptureRepository):
        self.repo = repo

    async def capture_image(self, file: UploadFile, course_code: str, section: str, student_id: str) -> CaptureResponse:
        return await self.repo.capture_image(file, course_code, section, student_id)

def get_capture_service(repo: CaptureRepository = Depends(get_capture_repository)):
    return CaptureService(repo)
