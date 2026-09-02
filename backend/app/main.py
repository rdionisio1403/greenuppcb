from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, Base
from app.dependencies import get_db
from app.routers import pcb, diagnosis, repair, test

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GreenUpPCB LIS",
    description="""
### 📊 [CLICK HERE TO VIEW FULL RELATIONAL DATABASE TABLE (LIVE SQL JOIN)](http://localhost:8000/view-table)

Laboratory Information System for PCB Intake, Diagnosis, Repair & Testing
    """,
    version="1.0.0",
    external_docs={
        "description": "👉 Open Relational Table View",
        "url": "http://localhost:8000/view-table"
    }
)

app.include_router(pcb.router)
app.include_router(diagnosis.router)
app.include_router(repair.router)
app.include_router(test.router)

@app.get("/view-table", response_class=HTMLResponse, tags=["Relational Table View"])
def view_full_relational_table(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            p.id AS pcb_id,
            p.internal_reference AS pcb_ref,
            p.equipment,
            p.status,
            d.fault_found AS diagnosis,
            r.actions_taken AS repair_done,
            t.test_type,
            t.result AS test_status
        FROM pcbs p
        LEFT JOIN diagnoses d ON p.id = d.pcb_id
        LEFT JOIN repairs r   ON p.id = r.pcb_id
        LEFT JOIN tests t     ON p.id = t.pcb_id
        ORDER BY p.id;
    """)
    rows = db.execute(query).fetchall()

    table_rows = ""
    for row in rows:
        table_rows += f"""
        <tr>
            <td style="font-weight:bold; color:#2563eb;">{row.pcb_id}</td>
            <td>{row.pcb_ref}</td>
            <td>{row.equipment}</td>
            <td><span style="background:#e0f2fe; padding:2px 8px; border-radius:4px;">{row.status}</span></td>
            <td style="background:#fefce8;">{row.diagnosis or '-'}</td>
            <td style="background:#f0fdf4;">{row.repair_done or '-'}</td>
            <td>{row.test_type or '-'}</td>
            <td><b>{row.test_status or '-'}</b></td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PCB Relational Lifecycle Table</title>
        <style>
            body {{ font-family: sans-serif; margin: 30px; background: #f8fafc; }}
            h2 {{ color: #1e293b; margin-bottom: 8px; }}
            p {{ color: #64748b; margin-top: 0; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; background: #ffffff; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border-radius: 8px; overflow: hidden; }}
            th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
            th {{ background-color: #0f172a; color: #ffffff; text-transform: uppercase; font-size: 12px; }}
            tr:hover {{ background-color: #f1f5f9; }}
        </style>
    </head>
    <body>
        <h2>GreenUp PCB — Consolidated Relational Database Table</h2>
        <p>Live SQL JOIN view: <code>pcbs &harr; diagnoses &harr; repairs &harr; tests</code></p>
        <table>
            <thead>
                <tr>
                    <th>PCB ID</th>
                    <th>Reference</th>
                    <th>Equipment</th>
                    <th>Status</th>
                    <th>Diagnosis (Diagnoses Table)</th>
                    <th>Repair Action (Repairs Table)</th>
                    <th>Test Type (Tests Table)</th>
                    <th>Test Result</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/", tags=["General"])
def root():
    return {"message": "GreenUpPCB LIS API is operational"}
