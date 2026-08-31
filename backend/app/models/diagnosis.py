from datetime import date
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from app.database import Base

class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    diagnosis_date = Column(Date, default=date.today, nullable=False)
    technician = Column(String(100), nullable=False)
    fault_found = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
