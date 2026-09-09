from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RepairCreate(BaseModel):
    repair_date: Optional[date] = Field(default_factory=date.today)
    technician: str
    actions_taken: str
    components_replaced: Optional[str] = None


class RepairRead(RepairCreate):
    id: int
    pcb_id: int
    repair_date: date

    model_config = ConfigDict(from_attributes=True)
