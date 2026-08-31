from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisRead

router = APIRouter(prefix="/pcbs/{pcb_id}/diagnoses", tags=["Diagnoses"])

@router.post("", response_model=DiagnosisRead, status_code=201)
def create_diagnosis(pcb_id: int, data: DiagnosisCreate, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    diagnosis = Diagnosis(pcb_id=pcb_id, **data.model_dump())
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)
    return diagnosis


@router.get("", response_model=List[DiagnosisRead])
def list_diagnoses(pcb_id: int, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Diagnosis).filter(Diagnosis.pcb_id == pcb_id).all()
