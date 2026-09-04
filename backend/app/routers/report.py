from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import traceback
import os

from app.dependencies import get_db
from app.models.pcb import PCB
from app.models.report import Report
from app.services.pdf_generator import generate_pcb_pdf

router = APIRouter(prefix="/pcbs/{pcb_id}/reports", tags=["Reports"])

@router.post("/generate", status_code=201)
def generate_report(pcb_id: int, db: Session = Depends(get_db)):
    # 1. Verify PCB exists
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    try:
        # 2. Gather lifecycle data via SQL query
        query = text("""
            SELECT 
                p.id, p.internal_reference, p.equipment, p.manufacturer, p.pcb_model, p.serial_number, p.status,
                d.findings, d.notes AS diag_notes,
                r.action, r.components_rep,
                t.notes AS test_notes, t.result AS test_result
            FROM pcbs p
            LEFT JOIN diagnoses d ON p.id = d.pcb_id
            LEFT JOIN repairs r   ON p.id = r.pcb_id
            LEFT JOIN tests t     ON p.id = t.pcb_id
            WHERE p.id = :pcb_id
            LIMIT 1;
        """)
        row = db.execute(query, {"pcb_id": pcb_id}).mappings().first()
        pcb_dict = dict(row) if row else {"id": pcb_id}

        # 3. Gather the LATEST image for each lifecycle category (distinct category)
        # Order of appearance in report: BEFORE -> DEFECT -> DURING -> AFTER
        img_records = db.execute(
            text("""
                SELECT DISTINCT ON (category) category, filename_path, id
                FROM images 
                WHERE pcb_id = :pcb_id 
                ORDER BY category, id DESC;
            """),
            {"pcb_id": pcb_id}
        ).fetchall()

        # Re-sort nicely in canonical lifecycle sequence
        canonical_order = {"before": 1, "defect": 2, "during": 3, "after": 4}
        sorted_images = sorted(
            [{"category": r.category, "path": r.filename_path} for r in img_records],
            key=lambda x: canonical_order.get(x["category"].lower(), 99)
        )

        # 4. Generate PDF
        pdf_rel_url = generate_pcb_pdf(pcb_dict, sorted_images)

        # 5. Insert report into DB
        new_report = Report(
            pcb_id=pcb_id,
            filename_path=pdf_rel_url
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        return {
            "message": "Service report successfully generated",
            "report_id": new_report.id,
            "pdf_url": new_report.filename_path,
            "generated_at": new_report.generated_at
        }

    except Exception as e:
        db.rollback()
        print("PDF GENERATION ERROR TRACEBACK:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Report build failed: {str(e)}")


@router.get("", status_code=200)
def list_reports(pcb_id: int, db: Session = Depends(get_db)):
    """List all generated reports metadata for the specified PCB."""
    pcb = db.query(PCB).filter(PCB.id == pcb_id).first()
    if not pcb:
        raise HTTPException(status_code=404, detail="PCB not found")

    reports = db.query(Report).filter(Report.pcb_id == pcb_id).order_by(Report.id.desc()).all()
    return reports


@router.get("/download", status_code=200)
def download_latest_report(pcb_id: int, db: Session = Depends(get_db)):
    """Stream and download the latest generated PDF service report for the PCB."""
    report = db.query(Report).filter(Report.pcb_id == pcb_id).order_by(Report.id.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="No report found for this PCB")

    file_path = report.filename_path.lstrip("/")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"PDF file not found on disk at {file_path}")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=os.path.basename(file_path)
    )
