from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisRead

router = APIRouter(prefix="/pcbs/{pcb_id}/diagnoses", tags=["Diagnoses"])

@router.post("", response_model=DiagnosisRead, status_code=status.HTTP_201_CREATED)
def create_diagnosis(pcb_id: int, data: DiagnosisCreate, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    diag_dict = data.model_dump(exclude_unset=True)
    if not diag_dict.get("diagnosis_date"):
        diag_dict["diagnosis_date"] = date.today()

    diagnosis = Diagnosis(pcb_id=pcb_id, **diag_dict)
    db.add(diagnosis)

    if pcb.status and pcb.status.lower() == "received":
        pcb.status = "in_diagnosis"

    db.commit()
    db.refresh(diagnosis)
    return diagnosis

@router.get("", response_model=List[DiagnosisRead])
def list_diagnoses(pcb_id: int, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Diagnosis).filter(Diagnosis.pcb_id == pcb_id).all()
