from datetime import date
from pydantic import BaseModel, ConfigDict
from app.schemas.diagnosis import DiagnosisRead
from app.schemas.repair import RepairRead
from app.schemas.test import TestRead
from app.schemas.image import ImageRead
from app.schemas.report import ReportRead

class PCBCreate(BaseModel):
    internal_reference: str
    customer_name: str
    equipment: str
    manufacturer: str | None = None
    pcb_model: str | None = None
    serial_number: str | None = None
    date_received: date
    failure_description: str

class PCBRead(PCBCreate):
    id: int
    status: str
    model_config = ConfigDict(from_attributes=True)

class PCBDetailRead(PCBRead):
    diagnoses: list[DiagnosisRead] = []
    repairs: list[RepairRead] = []
    tests: list[TestRead] = []
    images: list[ImageRead] = []
    reports: list[ReportRead] = []

class PCBUpdate(BaseModel):
    internal_reference: str | None = None
    customer_name: str | None = None
    equipment: str | None = None
    manufacturer: str | None = None
    pcb_model: str | None = None
    serial_number: str | None = None
    date_received: date | None = None
    failure_description: str | None = None
    status: str | None = None
