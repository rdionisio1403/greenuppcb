from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.test import Test
from app.schemas.test import TestCreate, TestRead

router = APIRouter(prefix="/pcbs/{pcb_id}/tests", tags=["Tests"])

@router.post("", response_model=TestRead, status_code=201)
def create_test(pcb_id: int, data: TestCreate, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    test = Test(pcb_id=pcb_id, **data.model_dump())
    db.add(test)
    db.commit()
    db.refresh(test)
    return test

@router.get("", response_model=List[TestRead])
def list_tests(pcb_id: int, db: Session = Depends(get_db)):
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    return db.query(Test).filter(Test.pcb_id == pcb_id).all()
