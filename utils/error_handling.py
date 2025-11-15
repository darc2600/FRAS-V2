"""
Centralized error handling and logging configuration
"""
import logging
import sys
from typing import Any, Dict
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging
def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log', mode='a')
        ]
    )

    # Set specific loggers
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# Custom exception classes
class DatabaseError(Exception):
    """Database operation error"""
    pass

class ValidationError(Exception):
    """Data validation error"""
    pass

class FaceRecognitionError(Exception):
    """Face recognition operation error"""
    pass

class FileUploadError(Exception):
    """File upload error"""
    pass

# Error response models
def create_error_response(status_code: int, message: str, details: Any = None) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        "error": True,
        "message": message,
        "status_code": status_code
    }
    if details:
        response["details"] = details
    return response

# Exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    logging.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.status_code, exc.detail)
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=create_error_response(500, "Internal server error")
    )

async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation exceptions"""
    logging.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content=create_error_response(422, "Validation error", str(exc))
    )

# Utility functions
def log_request(request: Request, response_status: int = None):
    """Log API requests"""
    logging.info(f"{request.method} {request.url} - Status: {response_status}")

def log_database_operation(operation: str, table: str, record_id: Any = None):
    """Log database operations"""
    message = f"DB {operation} on {table}"
    if record_id:
        message += f" (ID: {record_id})"
    logging.info(message)

def log_face_recognition(student_id: int, class_id: int, result: str):
    """Log face recognition operations"""
    logging.info(f"Face recognition: Student {student_id}, Class {class_id}, Result: {result}")

# Initialize logging
setup_logging()