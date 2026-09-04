from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel


class PCBBase(BaseModel):
    internal_reference: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    equipment: str
    manufacturer: Optional[str] = None
    pcb_model: Optional[str] = None
    serial_number: Optional[str] = None
    date_received: Optional[date] = None
    failure_description: Optional[str] = None
    status: Optional[str] = "received"


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
    status: Optional[str] = None


class PCBRead(PCBBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PCBDetailRead(PCBRead):
    pass
