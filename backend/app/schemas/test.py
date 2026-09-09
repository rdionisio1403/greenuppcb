from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TestCreate(BaseModel):
    test_date: Optional[date] = Field(default_factory=date.today)
    tester: str
    test_type: str
    result: str
    notes: Optional[str] = None


class TestRead(TestCreate):
    id: int
    pcb_id: int
    test_date: date

    model_config = ConfigDict(from_attributes=True)
