from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    filename_path = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), default=func.now(), nullable=False)

    # ORM relationship mapping back to PCB model
    pcb = relationship("PCB", back_populates="images")
