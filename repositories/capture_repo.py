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
        print(f"[DEBUG] ========== CAPTURE IMAGE START ==========")
        print(f"[DEBUG] Student ID: {student_id}")
        print(f"[DEBUG] Course Code: {course_code}, Section: {section}")
        print(f"[DEBUG] File name: {file.filename}")
        
        save_path = os.path.join("dataset", student_id)
        print(f"[DEBUG] Save path set to: {save_path}")
        print(f"[DEBUG] Absolute path: {os.path.abspath(save_path)}")
        os.makedirs(save_path, exist_ok=True)
        print(f"[DEBUG] Directory created/confirmed")
        
        # Get compression settings
        compression_quality = int(get_system_setting('image_compression_quality', '85'))
        max_size = int(get_system_setting('image_max_size', '640'))
        print(f"[DEBUG] Compression settings - Quality: {compression_quality}, Max size: {max_size}")
        
        # Save original temporarily
        temp_path = os.path.join(save_path, f"temp_{file.filename}")
        final_path = os.path.join(save_path, file.filename)
        print(f"[DEBUG] Temp path: {temp_path}")
        print(f"[DEBUG] Final path: {final_path}")
        
        try:
            print(f"[DEBUG] Writing file to temp location")
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"[DEBUG] File written to temp location successfully")
            
            # Compress the image
            print(f"[DEBUG] Compressing image")
            compress_face_image(
                temp_path, 
                final_path, 
                quality=compression_quality, 
                max_size=(max_size, max_size)
            )
            print(f"[DEBUG] Image compressed successfully")
            
            # Remove temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"[DEBUG] Temp file removed")
            
            # Verify file was saved
            if os.path.exists(final_path):
                file_size = os.path.getsize(final_path)
                print(f"[DEBUG] File verified at {final_path}, size: {file_size} bytes")
            else:
                print(f"[DEBUG] ERROR: File not found at final path!")
                
            print(f"[DEBUG] ========== CAPTURE IMAGE END (SUCCESS) ==========")
            return CaptureResponse(status="success", message=f"Compressed image saved to {final_path}")
            
        except Exception as e:
            print(f"[DEBUG] Exception during compression: {e}")
            # Fallback: save without compression
            print(f"[DEBUG] Attempting fallback: saving without compression")
            try:
                with open(final_path, "wb") as buffer:
                    if hasattr(file, 'file') and hasattr(file.file, 'seek'):
                        file.file.seek(0)  # Reset file pointer
                    shutil.copyfileobj(file.file, buffer)
                print(f"[DEBUG] File saved without compression")
            except Exception as e2:
                print(f"[DEBUG] ERROR during fallback save: {e2}")
                print(f"[DEBUG] ========== CAPTURE IMAGE END (FAILED) ==========")
                return CaptureResponse(status="error", message=f"Failed to save image: {str(e2)}")
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"[DEBUG] Temp file removed")
                
            print(f"[DEBUG] ========== CAPTURE IMAGE END (FALLBACK SUCCESS) ==========")
            return CaptureResponse(status="success", message=f"Image saved to {final_path} (compression failed: {str(e)})")

def get_capture_repository():
    return CaptureRepository()
