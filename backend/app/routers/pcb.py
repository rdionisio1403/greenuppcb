from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.models.pcb import PCB
from app.schemas.pcb import PCBCreate, PCBRead

router = APIRouter(prefix="/pcbs", tags=["PCBs"])

@router.post("", response_model=PCBRead, status_code=201)
def create_pcb(data: PCBCreate, db: Session = Depends(get_db)):
    existing = db.query(PCB).filter(PCB.internal_reference == data.internal_reference).first()
    if existing:
        raise HTTPException(status_code=409, detail="Internal reference already exists")

    pcb = PCB(**data.model_dump())
    db.add(pcb)
    db.commit()
    db.refresh(pcb)
    return pcb

@router.get("", response_model=List[PCBRead])
def list_pcbs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(PCB).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=PCBRead)
def get_pcb(id: int, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")
    return pcb

@router.patch("/{id}", response_model=PCBRead)
def update_pcb(id: int, data: PCBCreate, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    update_data = data.model_dump(exclude_unset=True)

    if "internal_reference" in update_data and update_data["internal_reference"] != pcb.internal_reference:
        existing = db.query(PCB).filter(PCB.internal_reference == update_data["internal_reference"]).first()
        if existing:
            raise HTTPException(status_code=409, detail="Internal reference already exists")

    for field, value in update_data.items():
        setattr(pcb, field, value)

    db.commit()
    db.refresh(pcb)
    return pcb
