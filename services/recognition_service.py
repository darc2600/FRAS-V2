# Uncomment if we want to use image compression
# from PIL import Image
# import os
from repositories.recognition_repo import RecognitionRepository, get_recognition_repository
from models.recognition import RecognitionResponse
from fastapi import UploadFile, Depends


# Uncomment if we want to use image compression
# def compress_face_image(input_path, output_path, quality=85, max_size=(640, 640)):
#     """
#     Compress face image for storage while maintaining recognition quality.
    
#     Args:
#         input_path: Path to input image
#         output_path: Path to save compressed image
#         quality: JPEG quality (1-100, higher = better quality)
#         max_size: Maximum dimensions (width, height)
#     """
#     with Image.open(input_path) as img:
#         # Convert to RGB if necessary
#         if img.mode not in ['RGB', 'L']:
#             img = img.convert('RGB')
        
#         # Resize if larger than max_size while maintaining aspect ratio
#         if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
#             img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
#         # Save with compression
#         img.save(output_path, 'JPEG', quality=quality, optimize=True)

class RecognitionService:
    def __init__(self, repo: RecognitionRepository):
        self.repo = repo

    async def recognize_face(self, file: UploadFile, class_id: int) -> RecognitionResponse:
        return await self.repo.recognize_face(file, class_id)

    async def mark_absents(self, class_id: int, date: str):
        return await self.repo.mark_absents(class_id, date)

def get_recognition_service(repo: RecognitionRepository = Depends(get_recognition_repository)):
    return RecognitionService(repo)
