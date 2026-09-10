from datetime import date
from typing import List, Generator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.test import Test
from app.models.pcb import PCB
from app.schemas.test import TestCreate, TestUpdate, TestRead

router = APIRouter(prefix="/pcbs/{pcb_id}/tests", tags=["Tests"])


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=TestRead, status_code=status.HTTP_201_CREATED)
def create_test(pcb_id: int, data: TestCreate, db: Session = Depends(get_db)):
    """Create a new test record for a specific PCB."""
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PCB with ID {pcb_id} not found."
        )
    
    test = Test(pcb_id=pcb_id, **data.model_dump())
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("", response_model=List[TestRead])
def list_tests(pcb_id: int, db: Session = Depends(get_db)):
    """Retrieve all test records for a specific PCB ordered by date descending."""
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PCB with ID {pcb_id} not found."
        )
    return db.query(Test).filter(Test.pcb_id == pcb_id).order_by(Test.test_date.desc()).all()


@router.patch("/{test_id}", response_model=TestRead)
def update_test(pcb_id: int, test_id: int, data: TestUpdate, db: Session = Depends(get_db)):
    """Update an existing test record, enforcing the 1-year immutability business rule."""
    test = db.query(Test).filter(Test.id == test_id, Test.pcb_id == pcb_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test record with ID {test_id} not found for PCB #{pcb_id}."
        )

    # Business Rule: Test records older than 365 days cannot be updated
    if test.test_date:
        age_in_days = (date.today() - test.test_date).days
        if age_in_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test records older than 1 year cannot be modified. Please create a new test record."
            )

    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(test, field, value)

    db.commit()
    db.refresh(test)
    return test
