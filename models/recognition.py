from pydantic import BaseModel
from typing import Optional

class RecognitionResponse(BaseModel):
    status: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    attendance_status: Optional[str] = None
    message: Optional[str] = None
