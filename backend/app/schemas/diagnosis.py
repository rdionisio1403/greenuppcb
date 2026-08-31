from datetime import date
from pydantic import BaseModel, ConfigDict


class DiagnosisCreate(BaseModel):
    diagnosis_date: date
    technician: str
    fault_found: str
    recommended_action: str | None = None

class DiagnosisRead(DiagnosisCreate):
    id: int
    pcb_id: int

    model_config = ConfigDict(from_attributes=True)
