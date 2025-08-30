from pydantic import BaseModel
from typing import List, Tuple

class AttendanceResponse(BaseModel):
    attendance: List[Tuple[str, str]]
