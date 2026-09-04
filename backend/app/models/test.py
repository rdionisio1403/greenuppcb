from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    test_date = Column("date", Date, nullable=False, default=func.current_date())
    tester = Column(String(100), nullable=True)
    test_type = Column(String(100), nullable=True)
    result = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)

    pcb = relationship("PCB", back_populates="tests")
