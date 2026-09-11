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

    # 2. PCBs by Status (case-insensitive keys)
    raw_status_counts = db.query(PCB.status, func.count(PCB.id)).group_by(PCB.status).all()
    status_counts = {}
    for status_val, count in raw_status_counts:
        if status_val:
            status_counts[str(status_val).lower()] = count

    # Count archived PCBs
    archived_count = 0
    if hasattr(PCB, "is_archived"):
        archived_count = db.query(func.count(PCB.id)).filter(PCB.is_archived == True).scalar() or 0
    elif "archived" in status_counts:
        archived_count = status_counts.get("archived", 0)

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

    tests_passed = db.query(func.count(Test.id)).filter(func.upper(Test.result) == "PASSED").scalar() or 0
    tests_failed = db.query(func.count(Test.id)).filter(func.upper(Test.result) == "FAILED").scalar() or 0
    pass_rate = round((tests_passed / tests_completed * 100), 1) if tests_completed > 0 else 100.0

    # 5. Recent PCBs for live queue
    recent_records = (
        db.query(PCB.id, PCB.internal_reference, PCB.serial_number, PCB.equipment, PCB.status, PCB.date_received)
        .order_by(PCB.id.desc())
        .limit(5)
        .all()
    )
    recent_pcbs = [
        {
            "id": r.id,
            "internal_reference": r.internal_reference,
            "serial_number": r.serial_number,
            "equipment": r.equipment,
            "status": r.status,
            "date_received": str(r.date_received) if r.date_received else "-"
        }
        for r in recent_records
    ]

    return {
        "total_pcbs": total_pcbs,
        "received": status_counts.get("registered", status_counts.get("received", 0)),
        "in_diagnosis": status_counts.get("in_diagnosis", 0),
        "repaired": status_counts.get("repaired", 0),
        "testing": status_counts.get("testing", 0),
        "completed": status_counts.get("completed", status_counts.get("closed", 0)),
        "archived": archived_count,
        "pcbs_this_month": pcbs_this_month,
        "repairs_completed": repairs_completed,
        "tests_completed": tests_completed,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "pass_rate": pass_rate,
        "recent_pcbs": recent_pcbs,
        "status_breakdown": status_counts
    }
