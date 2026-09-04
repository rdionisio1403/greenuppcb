from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ImageBase(BaseModel):
    category: str  # Lifecycle stages: before, during, after, defect
    filename_path: str

class ImageCreate(ImageBase):
    pass

class ImageRead(ImageBase):
    id: int
    pcb_id: int
    uploaded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
