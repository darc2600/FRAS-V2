from pydantic import BaseModel
from typing import List, Optional

class RegistrationResponse(BaseModel):
    status: str
    message: str
    image_paths: Optional[List[str]] = None
