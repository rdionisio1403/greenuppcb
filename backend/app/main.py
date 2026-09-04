from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from app.database import engine, Base
from app.dependencies import get_db
from app.routers import customer, pcb, diagnosis, repair, test, image, report

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

# Static file serving: /uploads maps directly to physical directory
os.makedirs("/opt/greenupcb/backend/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="/opt/greenupcb/backend/uploads"), name="uploads")

# Static file serving: /reports maps directly to physical reports directory
os.makedirs("/opt/greenupcb/backend/reports", exist_ok=True)
app.mount("/reports", StaticFiles(directory="/opt/greenupcb/backend/reports"), name="reports")

app.include_router(customer.router)
app.include_router(pcb.router)
app.include_router(diagnosis.router)
app.include_router(repair.router)
app.include_router(test.router)
app.include_router(image.router)
app.include_router(report.router)


@app.get("/view-table", response_class=HTMLResponse, tags=["Relational Table View"])
def view_full_relational_table(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            p.id AS pcb_id,
            p.internal_reference AS pcb_ref,
            COALESCE(c.name, p.customer_name, '-') AS customer,
            p.equipment,
            p.status,
            d.findings AS diagnosis,
            r.action AS repair_done,
            t.notes AS test_notes,
            t.result AS test_status,
            rep.filename_path AS report_path
        FROM pcbs p
        LEFT JOIN customers c ON p.customer_id = c.id
        LEFT JOIN diagnoses d ON p.id = d.pcb_id
        LEFT JOIN repairs r   ON p.id = r.pcb_id
        LEFT JOIN tests t     ON p.id = t.pcb_id
        LEFT JOIN reports rep ON p.id = rep.pcb_id
        ORDER BY p.id;
    """)
    rows = db.execute(query).fetchall()

    # Fetch and map all images per PCB ID
    img_records = db.execute(text("SELECT pcb_id, category, filename_path FROM images ORDER BY id;")).fetchall()
    pcb_images = {}
    for img in img_records:
        pcb_images.setdefault(img.pcb_id, []).append(img)

    # Color mapping for lifecycle inspection categories
    category_styles = {
        "before": {"bg": "#fee2e2", "color": "#b91c1c", "border": "#f87171"},  # Red: initial intake
        "defect": {"bg": "#ffedd5", "color": "#c2410c", "border": "#fb923c"},  # Orange: specific flaw
        "during": {"bg": "#e0f2fe", "color": "#0369a1", "border": "#7dd3fc"},  # Blue: repair in progress
        "after":  {"bg": "#dcfce7", "color": "#15803d", "border": "#86efac"}   # Green: post-repair cleaned
    }

    table_rows = ""
    for row in rows:
        imgs = pcb_images.get(row.pcb_id, [])
        if imgs:
            img_badges = []
            for im in imgs:
                cat = im.category.lower()
                style = category_styles.get(cat, {"bg": "#f1f5f9", "color": "#475569", "border": "#cbd5e1"})
                badge_style = f"background:{style['bg']}; color:{style['color']}; border:1px solid {style['border']};"
                img_badges.append(
                    f'<a href="{im.filename_path}" target="_blank" '
                    f'style="text-decoration:none; display:inline-block; margin:2px; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:700; {badge_style}">'
                    f'🔍 {im.category.upper()}</a>'
                )
            img_html = "".join(img_badges)
        else:
            img_html = '<span style="color:#94a3b8;">None</span>'

        rep_badge = f'<a href="{row.report_path}" target="_blank" style="color:#2563eb; font-weight:bold; text-decoration:none;">📄 Report</a>' if row.report_path else '<span style="color:#94a3b8;">None</span>'

        table_rows += f"""
        <tr>
            <td style="font-weight:bold; color:#2563eb;">{row.pcb_id}</td>
            <td>{row.pcb_ref}</td>
            <td style="font-weight:600; color:#334155;">{row.customer}</td>
            <td>{row.equipment}</td>
            <td><span style="background:#e0f2fe; padding:2px 8px; border-radius:4px;">{row.status}</span></td>
            <td style="background:#fefce8;">{row.diagnosis or '-'}</td>
            <td style="background:#f0fdf4;">{row.repair_done or '-'}</td>
            <td>{row.test_notes or '-'}</td>
            <td><b>{row.test_status or '-'}</b></td>
            <td>{img_html}</td>
            <td style="text-align:center;">{rep_badge}</td>
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
        <p>Live SQL JOIN view matching ER Diagram: <code>customers &harr; pcbs &harr; diagnoses &harr; repairs &harr; tests &harr; images &harr; reports</code></p>
        <table>
            <thead>
                <tr>
                    <th>PCB ID</th>
                    <th>Reference</th>
                    <th>Customer</th>
                    <th>Equipment</th>
                    <th>Status</th>
                    <th>Diagnosis (findings)</th>
                    <th>Repair (action)</th>
                    <th>Test Notes</th>
                    <th>Test Result</th>
                    <th>Images (Lifecycle)</th>
                    <th>Report</th>
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
