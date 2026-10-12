from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_csrf, require_admin
from app.audit import log_audit
from app.models.pcb import PCB
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisRead, DiagnosisUpdate

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

@router.patch("/{diagnosis_id}", response_model=DiagnosisRead)
def update_diagnosis(
    pcb_id: int,
    diagnosis_id: int,
    request: Request,
    data: DiagnosisUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    from app.routers.pcb import compute_is_archived

    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")
    if compute_is_archived(pcb):
        raise HTTPException(status_code=409, detail="Archived PCB records cannot be modified")

    diagnosis = (
        db.query(Diagnosis)
        .filter(Diagnosis.id == diagnosis_id, Diagnosis.pcb_id == pcb_id)
        .first()
    )
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis record not found")

    update_data = data.model_dump(exclude_unset=True)
    for field in ("technician", "fault_found", "diagnosis_date"):
        if field in update_data and update_data[field] is None:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")

    for field, value in update_data.items():
        setattr(diagnosis, field, value)

    db.commit()
    db.refresh(diagnosis)

    log_audit(
        db=db,
        event_type="DIAGNOSIS_UPDATED",
        request=request,
        user_id=current_user.id,
        details=f"diagnosis_id={diagnosis.id};pcb_id={pcb_id}",
    )
    return diagnosis

@router.delete("/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagnosis(
    pcb_id: int,
    diagnosis_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    csrf_session=Depends(require_csrf),
):
    from app.routers.pcb import compute_is_archived

    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")
    if compute_is_archived(pcb):
        raise HTTPException(
            status_code=409,
            detail="Archived PCB records cannot be modified",
        )

    diagnosis = (
        db.query(Diagnosis)
        .filter(Diagnosis.id == diagnosis_id, Diagnosis.pcb_id == pcb_id)
        .first()
    )
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis record not found")

    deleted_id = diagnosis.id
    db.delete(diagnosis)
    db.commit()

    log_audit(
        db=db,
        event_type="DIAGNOSIS_DELETED",
        request=request,
        user_id=current_user.id,
        details=f"diagnosis_id={deleted_id};pcb_id={pcb_id}",
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
