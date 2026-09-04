from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    contact_info = Column(String(200), nullable=True)
    reference = Column(String(100), nullable=True)

    # 1-N relationship: One customer can register multiple PCBs
    pcbs = relationship("PCB", back_populates="customer")
