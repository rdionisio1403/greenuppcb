from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    filename_path: str


class ReportRead(ReportCreate):
    id: int
    pcb_id: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
