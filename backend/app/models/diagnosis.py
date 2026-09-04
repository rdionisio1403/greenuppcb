from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    diagnosis_date = Column("date", Date, nullable=False, default=func.current_date())
    technician = Column(String(100), nullable=True)
    fault_found = Column("findings", Text, nullable=False)
    recommended_action = Column("notes", Text, nullable=True)

    pcb = relationship("PCB", back_populates="diagnoses")
