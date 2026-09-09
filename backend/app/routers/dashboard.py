from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.repair import Repair
from app.models.test import Test

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # 1. Total PCBs
    total_pcbs = db.query(func.count(PCB.id)).scalar() or 0

    # 2. PCBs by Status
    status_counts = dict(
        db.query(PCB.status, func.count(PCB.id)).group_by(PCB.status).all()
    )

    # 3. PCBs received this month
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    pcbs_this_month = (
        db.query(func.count(PCB.id))
        .filter(PCB.date_received >= start_of_month)
        .scalar()
        or 0
    )

    # 4. Completed repairs and tests
    repairs_completed = db.query(func.count(Repair.id)).scalar() or 0
    tests_completed = db.query(func.count(Test.id)).scalar() or 0

    return {
        "total_pcbs": total_pcbs,
        "received": status_counts.get("received", 0),
        "in_diagnosis": status_counts.get("in_diagnosis", 0),
        "repaired": status_counts.get("repaired", 0),
        "closed": status_counts.get("closed", 0),
        "pcbs_this_month": pcbs_this_month,
        "repairs_completed": repairs_completed,
        "tests_completed": tests_completed
    }
