import os
import shutil
from fastapi import UploadFile
from models.capture import CaptureResponse

class CaptureRepository:
    async def capture_image(self, file: UploadFile, course_code: str, section: str, student_id: str) -> CaptureResponse:
        save_path = os.path.join("dataset", student_id)
        os.makedirs(save_path, exist_ok=True)
        img_path = os.path.join(save_path, file.filename)
        with open(img_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return CaptureResponse(status="success", message=f"Image saved to {img_path}")

def get_capture_repository():
    return CaptureRepository()
