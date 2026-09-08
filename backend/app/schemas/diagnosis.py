from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DiagnosisBase(BaseModel):
    technician: str
    fault_found: str
    recommended_action: Optional[str] = None
    diagnosis_date: Optional[date] = None

class DiagnosisCreate(DiagnosisBase):
    pass

class DiagnosisRead(DiagnosisBase):
    id: int
    pcb_id: int
    diagnosis_date: date

    model_config = ConfigDict(from_attributes=True)
