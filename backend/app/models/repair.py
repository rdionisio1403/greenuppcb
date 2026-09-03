from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Repair(Base):
    __tablename__ = "repairs"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    repair_date = Column("date", Date, nullable=False, default=func.current_date())
    technician = Column(String(100), nullable=True)
    actions_taken = Column("action", Text, nullable=False)
    components_replaced = Column("components_rep", Text, nullable=True)
    notes = Column(Text, nullable=True)

    pcb = relationship("PCB", back_populates="repairs")
