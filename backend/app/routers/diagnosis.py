from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_csrf
from app.audit import log_audit
from app.models.pcb import PCB
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisRead

router = APIRouter(prefix="/pcbs/{pcb_id}/diagnoses", tags=["Diagnoses"])

@router.post("", response_model=DiagnosisRead, status_code=status.HTTP_201_CREATED)
def create_diagnosis(
    request: Request,
    pcb_id: int,
    data: DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    diag_dict = data.model_dump(exclude_unset=True)
    if not diag_dict.get("diagnosis_date"):
        diag_dict["diagnosis_date"] = date.today()

    diagnosis = Diagnosis(
        pcb_id=pcb_id,
        user_id=current_user.id,
        **diag_dict,
    )
    db.add(diagnosis)

    if pcb.status and pcb.status.lower() == "received":
        pcb.status = "in_diagnosis"

    db.commit()
    db.refresh(diagnosis)

    log_audit(
        db=db,
        event_type="DIAGNOSIS_CREATED",
        request=request,
        user_id=current_user.id,
        details=f"diagnosis_id={diagnosis.id};pcb_id={pcb_id}",
    )

    return diagnosis

@router.get("", response_model=List[DiagnosisRead])
def list_diagnoses(pcb_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Diagnosis).filter(Diagnosis.pcb_id == pcb_id).all()
