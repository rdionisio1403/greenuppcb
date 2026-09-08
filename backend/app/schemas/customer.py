from typing import Optional
from pydantic import BaseModel, ConfigDict

class CustomerBase(BaseModel):
    name: str
    contact_info: Optional[str] = None
    reference: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerRead(CustomerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
