from datetime import date
from pydantic import BaseModel, ConfigDict


class RepairCreate(BaseModel):
    repair_date: date
    technician: str
    actions_taken: str
    components_replaced: str | None = None


class RepairRead(RepairCreate):
    id: int
    pcb_id: int

    model_config = ConfigDict(from_attributes=True)
