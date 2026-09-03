from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PCB(Base):
    __tablename__ = "pcbs"

    id = Column(Integer, primary_key=True, index=True)
    internal_reference = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(200), nullable=False)
    equipment = Column(String(200), nullable=False)
    manufacturer = Column(String(200), nullable=True)
    pcb_model = Column(String(200), nullable=True)
    serial_number = Column(String(200), nullable=True)
    date_received = Column(Date, nullable=False, default=func.current_date())
    failure_description = Column(Text, nullable=True)
    status = Column(String(50), default="received", nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)

    diagnoses = relationship("Diagnosis", back_populates="pcb", cascade="all, delete-orphan")
    repairs = relationship("Repair", back_populates="pcb", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="pcb", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="pcb", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="pcb", cascade="all, delete-orphan")
