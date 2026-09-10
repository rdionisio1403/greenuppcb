from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict

from app.schemas.diagnosis import DiagnosisRead
from app.schemas.repair import RepairRead
from app.schemas.test import TestRead
from app.schemas.image import ImageRead
from app.schemas.report import ReportRead


class PCBStatus(str, Enum):
    REGISTERED = "REGISTERED"
    IN_DIAGNOSIS = "IN_DIAGNOSIS"
    REPAIRED = "REPAIRED"
    TESTING = "TESTING"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class PCBBase(BaseModel):
    internal_reference: str
    customer_id: Optional[int] = None
    equipment: str
    manufacturer: Optional[str] = None
    pcb_model: Optional[str] = None
    serial_number: Optional[str] = None
    date_received: Optional[date] = None
    failure_description: Optional[str] = None
    status: Optional[PCBStatus] = PCBStatus.REGISTERED


class PCBCreate(PCBBase):
    pass


class PCBUpdate(BaseModel):
    internal_reference: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    equipment: Optional[str] = None
    manufacturer: Optional[str] = None
    pcb_model: Optional[str] = None
    serial_number: Optional[str] = None
    date_received: Optional[date] = None
    failure_description: Optional[str] = None
    status: Optional[PCBStatus] = None


class PCBRead(PCBBase):
    id: int
    customer_name: Optional[str] = None
    created_at: datetime
    is_archived: bool = False

    model_config = ConfigDict(from_attributes=True)


class PCBDetailRead(PCBRead):
    diagnoses: List[DiagnosisRead] = []
    repairs: List[RepairRead] = []
    tests: List[TestRead] = []
    images: List[ImageRead] = []
    reports: List[ReportRead] = []

    model_config = ConfigDict(from_attributes=True)
