from datetime import date, datetime
from sqlalchemy import String, Text, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class PCB(Base):
    __tablename__ = "pcbs"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_reference: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(200))
    equipment: Mapped[str] = mapped_column(String(200))
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pcb_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    date_received: Mapped[date] = mapped_column(Date)
    failure_description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="received")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# Iliskisel baglantilar
    diagnoses = relationship("Diagnosis", backref="pcb", cascade="all, delete-orphan")
    repairs = relationship("Repair", backref="pcb", cascade="all, delete-orphan")
    tests = relationship("Test", backref="pcb", cascade="all, delete-orphan")
