from datetime import date
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from app.database import Base

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey("pcbs.id", ondelete="CASCADE"), nullable=False)
    test_date = Column(Date, default=date.today, nullable=False)
    tester = Column(String(100), nullable=False)
    test_type = Column(String(100), nullable=False)
    result = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
