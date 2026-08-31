from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.repair import Repair
from app.schemas.repair import RepairCreate, RepairRead

router = APIRouter(prefix="/pcbs/{pcb_id}/repairs", tags=["Repairs"])

@router.post("", response_model=RepairRead, status_code=201)
def create_repair(pcb_id: int, data: RepairCreate, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    repair = Repair(pcb_id=pcb_id, **data.model_dump())
    db.add(repair)
    db.commit()
    db.refresh(repair)
    return repair

@router.get("", response_model=List[RepairRead])
def list_repairs(pcb_id: int, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Repair).filter(Repair.pcb_id == pcb_id).all()
