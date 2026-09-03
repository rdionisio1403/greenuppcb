from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    filename_path = Column(String(255), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), default=func.now(), nullable=False)

    pcb = relationship("PCB", back_populates="reports")
