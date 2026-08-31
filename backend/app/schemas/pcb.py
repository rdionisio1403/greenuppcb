from datetime import date
from pydantic import BaseModel, ConfigDict

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
