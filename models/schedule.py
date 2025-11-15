from pydantic import BaseModel
from typing import Any, List

class ScheduleResponse(BaseModel):
    schedule: List[Any]
