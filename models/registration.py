from pydantic import BaseModel
from typing import List, Optional


class RegistrationRequest(BaseModel):
    student_id: str
    last_name: str
    first_name: str
    email: Optional[str] = None
    face_data_path: Optional[str] = None
    created_at: Optional[str] = None
    schedule: str

class RegistrationResponse(BaseModel):
    status: str
    message: str
    image_paths: Optional[List[str]] = None
