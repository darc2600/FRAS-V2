from pydantic import BaseModel
from typing import Any

class ScheduleResponse(BaseModel):
    schedule: Any
