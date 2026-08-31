from datetime import date
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from app.database import Base

class Repair(Base):
    __tablename__ = "repairs"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    repair_date = Column(Date, default=date.today, nullable=False)
    technician = Column(String(100), nullable=False)
    actions_taken = Column(Text, nullable=False)
    components_replaced = Column(Text, nullable=True)
