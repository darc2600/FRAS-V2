import os
import shutil
from fastapi import UploadFile
from models.capture import CaptureResponse
from PIL import Image
from services.db import get_connection

def get_system_setting(setting_key: str, default_value: str = "") -> str:
    """Get a system setting value from the database"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = ?", (setting_key,))
            result = cursor.fetchone()
            return result[0] if result else default_value
    except Exception:
        return default_value

def compress_face_image(input_path, output_path, quality=85, max_size=(640, 640)):
    """
    Compress face image for storage while maintaining recognition quality.
    
    Args:
        input_path: Path to input image
        output_path: Path to save compressed image
        quality: JPEG quality (1-100, higher = better quality)
        max_size: Maximum dimensions (width, height)
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            
            # Resize if larger than max_size while maintaining aspect ratio
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with compression
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
    except Exception as e:
        # If compression fails, just copy the original
        shutil.copy2(input_path, output_path)
        print(f"Image compression failed, copied original: {e}")

class CaptureRepository:
    async def capture_image(self, file: UploadFile, course_code: str, section: str, student_id: str) -> CaptureResponse:
        save_path = os.path.join("dataset", student_id)
        os.makedirs(save_path, exist_ok=True)
        
        # Get compression settings
        compression_quality = int(get_system_setting('image_compression_quality', '85'))
        max_size = int(get_system_setting('image_max_size', '640'))
        
        # Save original temporarily
        temp_path = os.path.join(save_path, f"temp_{file.filename}")
        final_path = os.path.join(save_path, file.filename)
        
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Compress the image
            compress_face_image(
                temp_path, 
                final_path, 
                quality=compression_quality, 
                max_size=(max_size, max_size)
            )
            
            # Remove temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return CaptureResponse(status="success", message=f"Compressed image saved to {final_path}")
            
        except Exception as e:
            # Fallback: save without compression
            with open(final_path, "wb") as buffer:
                if hasattr(file, 'file') and hasattr(file.file, 'seek'):
                    file.file.seek(0)  # Reset file pointer
                shutil.copyfileobj(file.file, buffer)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return CaptureResponse(status="success", message=f"Image saved to {final_path} (compression failed: {str(e)})")

def get_capture_repository():
    return CaptureRepository()
