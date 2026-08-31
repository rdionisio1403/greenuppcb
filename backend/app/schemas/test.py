from datetime import date
from pydantic import BaseModel, ConfigDict


class TestCreate(BaseModel):
    test_date: date
    tester: str
    test_type: str
    result: str
    notes: str | None = None


class TestRead(TestCreate):
    id: int
    pcb_id: int

    model_config = ConfigDict(from_attributes=True)
