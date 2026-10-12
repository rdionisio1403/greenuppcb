from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user, require_csrf, require_admin
from app.audit import log_audit
from app.models.pcb import PCB
from app.models.repair import Repair
from app.schemas.repair import RepairCreate, RepairRead, RepairUpdate

router = APIRouter(prefix="/pcbs/{pcb_id}/repairs", tags=["Repairs"])

@router.post("", response_model=RepairRead, status_code=201)
def create_repair(
    request: Request,
    pcb_id: int,
    data: RepairCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    csrf_session=Depends(require_csrf),
):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    repair = Repair(pcb_id=pcb_id, **data.model_dump())
    db.add(repair)
    db.commit()
    db.refresh(repair)

    log_audit(
        db=db,
        event_type="REPAIR_CREATED",
        request=request,
        user_id=current_user.id,
        details=f"repair_id={repair.id};pcb_id={pcb_id}",
    )

    return repair

@router.get("", response_model=List[RepairRead])
def list_repairs(pcb_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Repair).filter(Repair.pcb_id == pcb_id).all()

@router.patch("/{repair_id}", response_model=RepairRead)
def update_repair(
    pcb_id: int,
    repair_id: int,
    request: Request,
    data: RepairUpdate,
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

    repair = (
        db.query(Repair)
        .filter(Repair.id == repair_id, Repair.pcb_id == pcb_id)
        .first()
    )
    if not repair:
        raise HTTPException(status_code=404, detail="Repair record not found")

    update_data = data.model_dump(exclude_unset=True)
    for field in ("repair_date", "technician", "actions_taken"):
        if field in update_data and update_data[field] is None:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")

    for field, value in update_data.items():
        setattr(repair, field, value)

    db.commit()
    db.refresh(repair)

    log_audit(
        db=db,
        event_type="REPAIR_UPDATED",
        request=request,
        user_id=current_user.id,
        details=f"repair_id={repair.id};pcb_id={pcb_id}",
    )
    return repair

@router.delete("/{repair_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repair(
    pcb_id: int,
    repair_id: int,
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

    repair = (
        db.query(Repair)
        .filter(Repair.id == repair_id, Repair.pcb_id == pcb_id)
        .first()
    )
    if not repair:
        raise HTTPException(status_code=404, detail="Repair record not found")

    deleted_id = repair.id
    db.delete(repair)
    db.commit()

    log_audit(
        db=db,
        event_type="REPAIR_DELETED",
        request=request,
        user_id=current_user.id,
        details=f"repair_id={deleted_id};pcb_id={pcb_id}",
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
