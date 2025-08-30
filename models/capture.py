from pydantic import BaseModel
from typing import Optional

class CaptureResponse(BaseModel):
    status: str
    message: Optional[str] = None
