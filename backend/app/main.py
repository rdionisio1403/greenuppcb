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


@app.get("/view-table", response_class=HTMLResponse, tags=["General"])
def view_full_relational_table(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            p.id,
            COALESCE(p.serial_number, '-') AS serial_number,
            COALESCE(c.name, p.customer_name, '-') AS customer,
            p.equipment,
            p.status, rep.filename_path AS pdf_file,
            COALESCE(string_agg(DISTINCT CONCAT('• ', d.findings), '<br>'), '-') AS diagnosis,
            COALESCE(string_agg(DISTINCT CONCAT('• ', r.action), '<br>'), '-') AS repair_done,
            COALESCE(
                string_agg(
                    DISTINCT CONCAT(
                        '<div style="margin-bottom:6px; font-size:13px;">',
                        CASE 
                            WHEN UPPER(t.result) = 'PASSED' THEN '<span style="background:#dcfce7; color:#15803d; border:1px solid #86efac; padding:1px 6px; border-radius:4px; font-weight:700; font-size:11px;">PASSED</span> '
                            ELSE '<span style="background:#fee2e2; color:#b91c1c; border:1px solid #f87171; padding:1px 6px; border-radius:4px; font-weight:700; font-size:11px;">FAILED</span> '
                        END,
                        '<b>', COALESCE(t.test_type, 'General Test'), '</b>',
                        ' <span style="color:#64748b; font-size:11px;">(by ', t.tester, ')</span><br>',
                        '<span style="color:#334155; margin-left:8px;">', COALESCE(t.notes, '-'), '</span>',
                        '</div>'
                    ),
                    ''
                ),
                '-'
            ) AS test_evaluation
        FROM pcbs p
        LEFT JOIN customers c ON p.customer_id = c.id
        LEFT JOIN diagnoses d ON d.pcb_id = p.id
        LEFT JOIN repairs r ON r.pcb_id = p.id
        LEFT JOIN tests t ON t.pcb_id = p.id
        LEFT JOIN (
            SELECT DISTINCT ON (pcb_id) pcb_id, filename_path 
            FROM reports 
            ORDER BY pcb_id, id DESC
        ) rep ON rep.pcb_id = p.id
        GROUP BY p.id, c.name, p.customer_name, p.equipment, p.status, rep.filename_path
        ORDER BY p.id;
    """)
    
    images_query = text("""
        SELECT 
            i.pcb_id, 
            i.category, 
            i.filename_path, 
            COALESCE(i.technician, 'Technician') AS technician,
            COALESCE(t.test_type, (SELECT t2.test_type FROM tests t2 WHERE t2.pcb_id = i.pcb_id ORDER BY t2.id ASC LIMIT 1), 'Functional Test') AS test_type
        FROM images i
        LEFT JOIN tests t ON i.test_id = t.id
        ORDER BY i.id;
    """)
    
    im_map = {}
    for r in db.execute(images_query).fetchall():
        m = r._mapping
        pid = m["pcb_id"]
        if pid not in im_map:
            im_map[pid] = []
        tech = m["technician"] or "Technician"
        tt = m["test_type"]
        extra = f" • {tt}" if tt else ""
        cat = (m["category"] or "").lower()
        test_title = m["test_type"] or "Functional & Power Rail Test"

        # BEFORE -> Kırmızı, DURING -> Sarı, AFTER -> Yeşil, DEFECT -> Koyu Kırmızı
        if cat == "before":
            badge_bg = "#fef2f2"
            badge_color = "#b91c1c"
            badge_border = "#f87171"
            cat_icon = "🔍 BEFORE"
        elif cat == "during":
            badge_bg = "#fffbeb"
            badge_color = "#b45309"
            badge_border = "#fcd34d"
            cat_icon = "⚡ DURING"
        elif cat == "defect":
            badge_bg = "#450a0a"
            badge_color = "#fecaca"
            badge_border = "#dc2626"
            cat_icon = "⚠️ DEFECT"
        elif cat == "after":
            badge_bg = "#f0fdf4"
            badge_color = "#15803d"
            badge_border = "#86efac"
            cat_icon = "✅ AFTER"
        else:
            badge_bg = "#fef2f2"
            badge_color = "#b91c1c"
            badge_border = "#f87171"
            cat_icon = f"🔍 {cat.upper()}"

        badge = (
            f'<a href="{m["filename_path"]}" target="_blank" style="display:inline-flex; align-items:center; gap:6px; margin:3px 4px; padding:4px 9px; font-size:11px; font-weight:700; text-decoration:none; border-radius:6px; background:{badge_bg}; color:{badge_color}; border:1px solid {badge_border}; box-shadow:0 1px 2px rgba(0,0,0,0.05);">'
            f'{cat_icon} <span style="font-size:10px; font-weight:700; color:#1e293b; background:#ffffff; padding:2px 7px; border-radius:4px; border:1px solid {badge_border};">{test_title}</span></a>'
        )
        im_map[pid].append(badge)
        
    records = db.execute(query).fetchall()
    table_rows = ""
    for r in records:
        m = r._mapping
        pid = m["id"]
        imgs_html = "".join(im_map.get(pid, [])) or '<span style="color:#9ca3af; font-size:12px;">No images</span>'
        table_rows += f"""
        <tr>
            <td style="font-weight: 800; color: #0f172a;">#{pid}</td>
            <td style="font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 700; color: #0284c7; background: #f0f9ff; padding: 6px 10px; border-radius: 6px; border: 1px solid #e0f2fe; display: inline-block;">{m['serial_number']}</td>
            <td style="font-weight: 700; color: #0f172a;">{m['customer']}</td>
            <td style="color: #1e293b; font-weight: 600;">{m['equipment']}</td>
            <td><span class="badge-status">{m['status']}</span></td>
            <td style="color: #1e293b; line-height: 1.6;">{m['diagnosis']}</td>
            <td style="color: #1e293b; line-height: 1.6;">{m['repair_done']}</td>
            <td>{m['test_evaluation']}</td>
            <td>{imgs_html}</td>
            <td style="text-align: center;">{f'<a href="{m["pdf_file"]}" target="_blank" class="btn-pdf">📄 PDF</a>' if m.get('pdf_file') else f'<a href="/pcbs/{pid}/reports/download" target="_blank" class="btn-pdf">📄 PDF</a>'}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GreenUpPCB - Lifecycle Intelligence View</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                background: linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 100%); 
                margin: 0; 
                padding: 24px 32px; 
                color: #0f172a; 
            }}
            .page-wrapper {{
                background: #ffffff;
                border-radius: 14px;
                box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
                border: 1px solid #cbd5e1;
                overflow: hidden;
            }}
            .header-bar {{
                padding: 18px 24px;
                background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 12px;
            }}
            .header-bar h1 {{
                margin: 0;
                font-size: 19px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: -0.01em;
            }}
            .sync-badge {{
                font-size: 12px;
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border: 1px solid rgba(52, 211, 153, 0.4);
                padding: 4px 12px;
                border-radius: 9999px;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }}
            .table-responsive {{
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}
            table {{
                width: 100%;
                min-width: 1280px;
                border-collapse: separate;
                border-spacing: 0;
                text-align: left;
            }}
            th {{
                background-color: #f8fafc;
                padding: 14px 18px;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: #475569;
                border-bottom: 2px solid #e2e8f0;
                white-space: nowrap;
            }}
            td {{
                padding: 16px 18px;
                vertical-align: top;
                border-bottom: 1px solid #f1f5f9;
                font-size: 13px;
            }}
            tr:hover td {{
                background-color: #f8fafc;
            }}
            .badge-status {{
                display: inline-block;
                background: #e0f2fe;
                color: #0369a1;
                border: 1px solid #7dd3fc;
                padding: 4px 9px;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.03em;
                white-space: nowrap;
                box-shadow: 0 1px 2px rgba(2, 132, 199, 0.08);
            }}
            .btn-pdf {{
                display: inline-block;
                color: #1d4ed8;
                font-weight: 700;
                text-decoration: none;
                padding: 5px 12px;
                border-radius: 6px;
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                box-shadow: 0 1px 2px rgba(29, 78, 216, 0.06);
            }}
            .btn-pdf:hover {{
                background: #dbeafe;
            }}
        </style>
    </head>
    <body>
        <div class="page-wrapper">
            <div class="header-bar">
                <h1>GreenUpPCB - Full Lifecycle Intelligence Table</h1>
                <span class="sync-badge">● Real-time DB Sync</span>
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 60px;">ID</th>
                            <th style="width: 140px;">Serial</th>
                            <th style="width: 160px;">Customer</th>
                            <th style="width: 180px;">Equipment</th>
                            <th style="width: 120px;">Status</th>
                            <th style="min-width: 240px;">Diagnosis Findings</th>
                            <th style="min-width: 240px;">Repairs Done</th>
                            <th style="min-width: 300px;">Test Results & Evaluation</th>
                            <th style="min-width: 160px;">Images</th>
                            <th style="width: 80px; text-align: center;">Report</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/", tags=["General"])
def root():
    return {"message": "GreenUpPCB LIS API is operational"}
