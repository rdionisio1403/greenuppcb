from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from app.database import engine, Base
from app.dependencies import get_db
from app.routers import dashboard,  customer, pcb, diagnosis, repair, test, image, report

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
app.include_router(dashboard.router)


@app.get("/view-table", response_class=HTMLResponse, tags=["General"])
def view_full_relational_table(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            p.id,
            COALESCE(p.serial_number, '-') AS serial_number,
            COALESCE(c.name, p.customer_name, '-') AS customer,
            p.equipment,
            p.status, 
            p.customer_id,
            rep.filename_path AS pdf_file,
            COALESCE(string_agg(DISTINCT CONCAT('• ', d.findings), '<br>'), '-') AS diagnosis,
            COALESCE(string_agg(DISTINCT CONCAT('• ', r.action), '<br>'), '-') AS repair_done
        FROM pcbs p
        LEFT JOIN customers c ON p.customer_id = c.id
        LEFT JOIN diagnoses d ON d.pcb_id = p.id
        LEFT JOIN repairs r ON r.pcb_id = p.id
        LEFT JOIN (
            SELECT DISTINCT ON (pcb_id) pcb_id, filename_path 
            FROM reports 
            ORDER BY pcb_id, id DESC
        ) rep ON rep.pcb_id = p.id
        GROUP BY p.id, c.name, p.customer_name, p.equipment, p.status, p.customer_id, rep.filename_path
        ORDER BY p.id DESC;
    """)

    tests_query = text("""
        SELECT 
            id,
            pcb_id,
            date AS test_date,
            tester,
            test_type,
            result,
            notes,
            (CURRENT_DATE - date) AS age_days
        FROM tests
        ORDER BY id ASC;
    """)

    test_rows = db.execute(tests_query).fetchall()
    test_map = {}
    for t in test_rows:
        tm = t._mapping
        pid = tm["pcb_id"]
        if pid not in test_map:
            test_map[pid] = []
        test_map[pid].append(tm)

    images_query = text("""
        SELECT 
            i.pcb_id, 
            i.category, 
            i.filename_path, 
            COALESCE(NULLIF(i.technician, 'Technician'), t.tester, 'Technician') AS technician,
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
        cat = (m["category"] or "").lower()
        test_title = m["test_type"] or "Functional & Power Rail Test"

        if cat == "before":
            badge_bg = "#fef2f2"; badge_color = "#b91c1c"; badge_border = "#f87171"; cat_icon = "🔍 BEFORE"
        elif cat == "during":
            badge_bg = "#fffbeb"; badge_color = "#b45309"; badge_border = "#fcd34d"; cat_icon = "⚡ DURING"
        elif cat == "defect":
            badge_bg = "#450a0a"; badge_color = "#fecaca"; badge_border = "#dc2626"; cat_icon = "⚠️ DEFECT"
        elif cat == "after":
            badge_bg = "#f0fdf4"; badge_color = "#15803d"; badge_border = "#86efac"; cat_icon = "✅ AFTER"
        else:
            badge_bg = "#fef2f2"; badge_color = "#b91c1c"; badge_border = "#f87171"; cat_icon = f"🔍 {cat.upper()}"

        badge = (
            f'<a href="{m["filename_path"]}" target="_blank" style="display:inline-flex; align-items:center; gap:6px; margin:3px 4px; padding:4px 9px; font-size:11px; font-weight:700; text-decoration:none; border-radius:6px; background:{badge_bg}; color:{badge_color}; border:1px solid {badge_border}; box-shadow:0 1px 2px rgba(0,0,0,0.05);">'
            f'{cat_icon} <span style="font-size:10px; font-weight:700; color:#1e293b; background:#ffffff; padding:3px 7px; border-radius:4px; border:1px solid {badge_border}; line-height:1.2; text-align:center;">{test_title}<br><span style="font-size:9px; color:#64748b; font-weight:600;">(by {tech})</span></span></a>'
        )
        im_map[pid].append(badge)
        
    records = db.execute(query).fetchall()
    table_rows = ""
    for r in records:
        m = r._mapping
        pid = m["id"]
        imgs_html = "".join(im_map.get(pid, [])) or '<span style="color:#9ca3af; font-size:12px;">No images</span>'
        
        pcb_tests = test_map.get(pid, [])
        all_tests_archived = False
        if pcb_tests:
            min_age = min((t["age_days"] for t in pcb_tests if t["age_days"] is not None), default=0)
            if min_age > 365:
                all_tests_archived = True

            test_items = []
            for t in pcb_tests:
                is_passed = (t["result"] or "").upper() == "PASSED"
                res_badge = '<span style="background:#dcfce7; color:#15803d; border:1px solid #86efac; padding:1px 6px; border-radius:4px; font-weight:700; font-size:11px;">PASSED</span>' if is_passed else '<span style="background:#fee2e2; color:#b91c1c; border:1px solid #f87171; padding:1px 6px; border-radius:4px; font-weight:700; font-size:11px;">FAILED</span>'
                tester_str = f' <span style="color:#64748b; font-size:11px;">(by {t["tester"]})</span>' if t["tester"] else ''
                
                age = t["age_days"] if t["age_days"] is not None else 0
                lock_indicator = '<span style="display:inline-block; font-size:10px; font-weight:700; color:#b91c1c; background:#fee2e2; border:1px solid #fca5a5; border-radius:4px; padding:1px 5px; margin-left:6px;" title="Record older than 1 year (Immutable)">🔒 Locked (>1 yr)</span>' if age > 365 else ''
                
                test_items.append(
                    f'<div style="margin-bottom:8px; font-size:13px; border-bottom:1px dashed #e2e8f0; padding-bottom:4px;">'
                    f'{res_badge} <b>{t["test_type"] or "General Test"}</b>{tester_str} {lock_indicator}'
                    f'<br><span style="color:#334155; margin-left:4px;">{t["notes"] or "-"}</span>'
                    f'</div>'
                )
            test_evaluation_html = "".join(test_items)
        else:
            test_evaluation_html = '<span style="color:#94a3b8; font-size:12px;">No tests recorded</span>'

        serial_clean = m['serial_number'].replace("'", "\\'")
        status_clean = (m['status'] or '').replace("'", "\\'")
        customer_clean = (m['customer'] or '').replace("'", "\\'")
        equip_clean = (m['equipment'] or '').replace("'", "\\'")
        cust_id = m['customer_id'] or 'null'
        
        status_badge = f'<span class="badge-status">{m["status"]}</span>'
        if all_tests_archived:
            status_badge += ' <span style="font-size:10px; font-weight:700; background:#fef2f2; color:#b91c1c; border:1px solid #fca5a5; border-radius:4px; padding:2px 5px; display:inline-block; margin-top:4px;">🔒 ARCHIVED</span>'

        table_rows += f"""
        <tr>
            <td style="font-weight: 800; color: #0f172a;">#{pid}</td>
            <td style="font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 700; color: #0284c7; background: #f0f9ff; padding: 6px 10px; border-radius: 6px; border: 1px solid #e0f2fe; display: inline-block;">{m['serial_number']}</td>
            <td style="font-weight: 700; color: #0f172a;">{m['customer']}</td>
            <td style="color: #1e293b; font-weight: 600;">{m['equipment']}</td>
            <td>{status_badge}</td>
            <td style="color: #1e293b; line-height: 1.6;">{m['diagnosis']}</td>
            <td style="color: #1e293b; line-height: 1.6;">{m['repair_done']}</td>
            <td>{test_evaluation_html}</td>
            <td>{imgs_html}</td>
            <td style="text-align: center;">{f'<a href="{m["pdf_file"]}" target="_blank" class="btn-pdf">📄 PDF</a>' if m.get('pdf_file') else f'<a href="/pcbs/{pid}/reports/download" target="_blank" class="btn-pdf">📄 PDF</a>'}</td>
            <td style="text-align: center;">
                <button onclick="openManageModal({pid}, '{serial_clean}', '{status_clean}', '{customer_clean}', '{equip_clean}', {cust_id})" class="btn-manage">⚙️ Manage</button>
            </td>
        </tr>
        """

    html_head_and_body = f"""
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
                min-width: 1360px;
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
            .btn-manage {{
                cursor: pointer;
                display: inline-block;
                color: #0f172a;
                font-weight: 700;
                padding: 5px 12px;
                border-radius: 6px;
                background: #f1f5f9;
                border: 1px solid #cbd5e1;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                transition: all 0.15s ease-in-out;
            }}
            .btn-manage:hover {{
                background: #0284c7;
                color: #ffffff;
                border-color: #0284c7;
            }}
            
            .modal-backdrop {{
                display: none;
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(15, 23, 42, 0.6);
                backdrop-filter: blur(4px);
                z-index: 1000;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .modal-box {{
                background: #ffffff;
                border-radius: 12px;
                padding: 24px;
                width: 100%;
                max-width: 620px;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                border: 1px solid #e2e8f0;
            }}
            .section-title {{
                font-size: 13px;
                font-weight: 800;
                color: #0f172a;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-top: 18px;
                margin-bottom: 8px;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 4px;
            }}
            .test-edit-row {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 10px;
            }}
            .test-edit-row.locked {{
                background: #f1f5f9;
                opacity: 0.75;
                border-color: #cbd5e1;
            }}
            .archived-alert {{
                background: #fef2f2;
                border: 1px solid #f87171;
                border-radius: 8px;
                padding: 12px 14px;
                color: #991b1b;
                font-size: 12px;
                margin-bottom: 16px;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <div class="page-wrapper">
            <div class="header-bar">
                <h1>GreenUpPCB - Full Lifecycle Intelligence Table</h1>
                <span class="sync-badge">● Real-time DB Sync</span>
            </div>
                        <div style="padding: 16px 24px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 10px; flex: 1; max-width: 480px;">
                    <span style="font-size: 16px;">🔍</span>
                    <input type="text" id="tableSearchInput" placeholder="Search reference, serial, status, archived, customer, tests..." 
                           style="width: 100%; padding: 8px 14px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; outline: none; background: #ffffff; color: #0f172a;" 
                           oninput="onSearchChange(this.value)" />
                </div>
                <div id="tableCounter" style="font-size: 13px; color: #64748b; font-weight: 500;">
                    Loading items...
                </div>
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
                            <th style="width: 100px; text-align: center;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            <div style="padding: 14px 24px; background: #ffffff; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: #64748b;">
                    <span>Rows per page:</span>
                    <select id="pageSizeSelect" onchange="changePageSize(this.value)" style="padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 12px; background: #fff;">
                        <option value="5">5</option>
                        <option value="10" selected>10</option>
                        <option value="25">25</option>
                        <option value="all">All</option>
                    </select>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <button id="btnPrevPage" onclick="prevPage()" style="padding: 6px 14px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; color: #334155;">Previous</button>
                    <span id="pageIndicator" style="font-size: 13px; font-weight: 600; color: #334155; margin: 0 4px;">Page 1</span>
                    <button id="btnNextPage" onclick="nextPage()" style="padding: 6px 14px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; color: #334155;">Next</button>
                </div>
            </div>
        </div>

        <div id="manageModal" class="modal-backdrop">
            <div class="modal-box">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <h3 id="modalTitle" style="margin:0; font-size:18px; color:#0f172a;">Manage PCB</h3>
                        <span id="modalSubtitle" style="font-size:12px; color:#64748b;">Serial: -</span>
                    </div>
                    <button onclick="closeManageModal()" style="border:none; background:none; font-size:20px; cursor:pointer; color:#64748b;">&times;</button>
                </div>

                <div id="archivedNotice" style="display:none;" class="archived-alert">
                    <b>⚠️ 1-YEAR LIFECYCLE EXPIRED (ARCHIVED):</b><br>
                    All testing activity for this unit is older than 1 year (365 days). Under laboratory policy, this historical record is completely sealed and immutable.<br>
                    Click <b>"Re-Intake PCB (Create New ID)"</b> to issue a new service intake and begin a fresh lifecycle for this board.
                </div>

                <div class="section-title">1. Operational Status</div>
                <div style="margin-bottom: 14px;">
                    <label style="display:block; font-size:12px; font-weight:700; color:#334155; margin-bottom:4px;">PCB Status</label>
                    <select id="pcbStatusSelect" style="width:100%; padding:8px 10px; border-radius:6px; border:1px solid #cbd5e1; font-size:13px;">
                        <option value="REGISTERED">REGISTERED</option>
                        <option value="IN_DIAGNOSIS">IN_DIAGNOSIS</option>
                        <option value="REPAIRING">REPAIRING</option>
                        <option value="TESTING">TESTING</option>
                        <option value="COMPLETED">COMPLETED</option>
                        <option value="SCRAPPED">SCRAPPED</option>
                    </select>
                </div>

                <div class="section-title">2. Test History & Evaluation</div>
                <div id="testsContainer" style="margin-bottom:16px;">
                    <div style="text-align:center; padding:12px; color:#64748b; font-size:12px;">Loading test records...</div>
                </div>

                <div id="addTestSection">
                    <div class="section-title">3. Conduct New Test (Active Lifecycle)</div>
                    <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px; margin-bottom:20px;">
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:8px;">
                            <div>
                                <label style="display:block; font-size:11px; font-weight:700; color:#166534; margin-bottom:2px;">Test Type</label>
                                <input type="text" id="newTestType" placeholder="e.g. Functional & Load Test" style="width:100%; padding:6px 8px; border-radius:6px; border:1px solid #86efac; font-size:12px;" />
                            </div>
                            <div>
                                <label style="display:block; font-size:11px; font-weight:700; color:#166534; margin-bottom:2px;">Tester (Technician)</label>
                                <input type="text" id="newTestTester" placeholder="e.g. Sema" style="width:100%; padding:6px 8px; border-radius:6px; border:1px solid #86efac; font-size:12px;" />
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 2fr; gap:10px; margin-bottom:8px;">
                            <div>
                                <label style="display:block; font-size:11px; font-weight:700; color:#166534; margin-bottom:2px;">Result</label>
                                <select id="newTestResult" style="width:100%; padding:6px 8px; border-radius:6px; border:1px solid #86efac; font-size:12px;">
                                    <option value="Passed">Passed</option>
                                    <option value="Failed">Failed</option>
                                </select>
                            </div>
                            <div>
                                <label style="display:block; font-size:11px; font-weight:700; color:#166534; margin-bottom:2px;">Notes</label>
                                <input type="text" id="newTestNotes" placeholder="Observations, voltages, etc." style="width:100%; padding:6px 8px; border-radius:6px; border:1px solid #86efac; font-size:12px;" />
                            </div>
                        </div>
                        <button type="button" onclick="submitNewTest()" style="cursor:pointer; background:#16a34a; color:#ffffff; border:none; border-radius:6px; padding:6px 12px; font-weight:700; font-size:11px;">+ Add Test Entry</button>
                    </div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #e2e8f0; padding-top:14px;">
                    <div>
                        <button id="btnReIntake" type="button" onclick="reIntakePcb()" style="display:none; cursor:pointer; padding:8px 14px; border-radius:6px; border:1px solid #16a34a; background:#dcfce7; color:#15803d; font-weight:700; font-size:12px;">📋 Re-Intake PCB (Create New ID)</button>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button type="button" onclick="closeManageModal()" style="cursor:pointer; padding:8px 16px; border-radius:6px; border:1px solid #cbd5e1; background:#f8fafc; font-weight:600; font-size:13px; color:#475569;">Close</button>
                        <button id="btnSaveUpdates" type="button" onclick="saveStatusAndActiveTests()" style="cursor:pointer; padding:8px 18px; border-radius:6px; border:none; background:#0284c7; color:#ffffff; font-weight:700; font-size:13px;">Save Updates</button>
                    </div>
                </div>
            </div>
        </div>
    """

    js_script = """
        <script>
            let activePcbId = null;
            let activeSerialNumber = '';
            let activeEquipment = '';
            let activeCustomerId = null;
            let activeCustomerName = '';
            let currentPcbTests = [];

            async function openManageModal(pcbId, serialNumber, currentStatus, customerName, equipment, customerId) {
                activePcbId = pcbId;
                activeSerialNumber = serialNumber;
                activeEquipment = equipment;
                activeCustomerId = customerId;
                activeCustomerName = customerName;

                document.getElementById('modalTitle').innerText = 'Manage PCB #' + pcbId;
                document.getElementById('modalSubtitle').innerText = 'Serial: ' + serialNumber + ' | ' + equipment;
                document.getElementById('pcbStatusSelect').value = currentStatus;
                document.getElementById('manageModal').style.display = 'flex';

                await loadPcbTests(pcbId);
            }

            function closeManageModal() {
                document.getElementById('manageModal').style.display = 'none';
            }

            async function loadPcbTests(pcbId) {
                const container = document.getElementById('testsContainer');
                container.innerHTML = '<div style="color:#64748b; font-size:12px;">Loading test history...</div>';

                try {
                    const response = await fetch('/pcbs/' + pcbId + '/tests');
                    if (!response.ok) throw new Error('Failed to load tests');
                    currentPcbTests = await response.json();

                    const today = new Date();
                    let hasRecentActiveTest = false;

                    if (currentPcbTests.length === 0) {
                        container.innerHTML = '<div style="color:#94a3b8; font-size:12px; font-style:italic;">No test records found for this unit.</div>';
                        hasRecentActiveTest = true; // Brand new intake without tests is active
                    } else {
                        let html = '';
                        currentPcbTests.forEach(test => {
                            const testDate = new Date(test.test_date);
                            const diffDays = Math.floor((today - testDate) / (1000 * 60 * 60 * 24));
                            const isLocked = diffDays > 365;
                            if (!isLocked) hasRecentActiveTest = true;

                            html += '<div class="test-edit-row ' + (isLocked ? 'locked' : '') + '">' +
                                '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">' +
                                    '<div><b style="font-size:12px; color:#0f172a;">' + (test.test_type || 'General Test') + '</b>' +
                                    '<span style="font-size:11px; color:#64748b;"> (' + test.test_date + ')</span></div>' +
                                    (isLocked ? '<span style="font-size:11px; font-weight:700; color:#b91c1c;">🔒 Locked (>1 Yr)</span>' : '<span style="font-size:11px; font-weight:700; color:#15803d;">✏️ Editable</span>') +
                                '</div>' +
                                '<div style="display:grid; grid-template-columns:110px 1fr; gap:8px;">' +
                                    '<select id="test_res_' + test.id + '" ' + (isLocked ? 'disabled' : '') + ' style="padding:4px 6px; border-radius:4px; border:1px solid #cbd5e1; font-size:12px;">' +
                                        '<option value="Passed" ' + (test.result.toLowerCase() === 'passed' ? 'selected' : '') + '>Passed</option>' +
                                        '<option value="Failed" ' + (test.result.toLowerCase() === 'failed' ? 'selected' : '') + '>Failed</option>' +
                                    '</select>' +
                                    '<input type="text" id="test_notes_' + test.id + '" value="' + (test.notes || '').replace(/"/g, '&quot;') + '" ' + (isLocked ? 'disabled' : '') + ' placeholder="' + (isLocked ? 'Locked for auditing' : 'Test notes...') + '" style="padding:4px 8px; border-radius:4px; border:1px solid #cbd5e1; font-size:12px; width:100%;" />' +
                                '</div>' +
                            '</div>';
                        });
                        container.innerHTML = html;
                    }

                    // Smart Archive Decision:
                    // If ALL tests on this PCB are >365 days old -> Entire lifecycle is expired/archived.
                    // If there is at least ONE test <=365 days -> PCB is currently active in laboratory!
                    const isEntirePcbArchived = !hasRecentActiveTest;

                    if (isEntirePcbArchived) {
                        document.getElementById('archivedNotice').style.display = 'block';
                        document.getElementById('pcbStatusSelect').disabled = true;
                        document.getElementById('addTestSection').style.display = 'none';
                        document.getElementById('btnSaveUpdates').style.display = 'none';
                        document.getElementById('btnReIntake').style.display = 'inline-block';
                    } else {
                        document.getElementById('archivedNotice').style.display = 'none';
                        document.getElementById('pcbStatusSelect').disabled = false;
                        document.getElementById('addTestSection').style.display = 'block';
                        document.getElementById('btnSaveUpdates').style.display = 'inline-block';
                        document.getElementById('btnReIntake').style.display = 'none';
                    }

                } catch (err) {
                    container.innerHTML = '<div style="color:#b91c1c; font-size:12px;">Error loading tests: ' + err.message + '</div>';
                }
            }

            async function reIntakePcb() {
                if (!confirm('This action will archive PCB #' + activePcbId + ' and register a brand new PCB intake with a new ID for serial ' + activeSerialNumber + '. Continue?')) {
                    return;
                }

                try {
                    const uniqueRef = 'RE-' + (activeSerialNumber !== '-' ? activeSerialNumber : 'PCB') + '-' + Date.now().toString().slice(-5);
                    const todayStr = new Date().toISOString().split('T')[0];

                    const payload = {
                        internal_reference: uniqueRef,
                        serial_number: activeSerialNumber !== '-' ? activeSerialNumber : null,
                        equipment: activeEquipment !== '-' ? activeEquipment : 'General PCB Unit',
                        date_received: todayStr,
                        status: 'REGISTERED'
                    };
                    if (activeCustomerId) payload.customer_id = activeCustomerId;

                    const res = await fetch('/pcbs', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (res.ok) {
                        const newPcb = await res.json();
                        alert('Success! New PCB intake created with ID #' + newPcb.id + ' (Ref: ' + uniqueRef + '). The original record remains preserved as an immutable archive.');
                        closeManageModal();
                        window.location.reload();
                    } else {
                        const err = await res.json();
                        let errorMsg = 'Unknown error';
                        if (typeof err.detail === 'string') {
                            errorMsg = err.detail;
                        } else if (Array.isArray(err.detail)) {
                            errorMsg = err.detail.map(d => d.msg + ' (' + d.loc.join('.') + ')').join('; ');
                        }
                        alert('Could not create new intake: ' + errorMsg);
                    }
                } catch (e) {
                    alert('Network error: ' + e.message);
                }
            }

            async function submitNewTest() {
                const testType = document.getElementById('newTestType').value.trim();
                const tester = document.getElementById('newTestTester').value.trim();
                const result = document.getElementById('newTestResult').value;
                const notes = document.getElementById('newTestNotes').value.trim();

                if (!testType || !tester) {
                    alert('Please specify Test Type and Tester name.');
                    return;
                }

                try {
                    const response = await fetch('/pcbs/' + activePcbId + '/tests', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            test_type: testType,
                            tester: tester,
                            result: result,
                            notes: notes
                        })
                    });

                    if (response.ok) {
                        document.getElementById('newTestType').value = '';
                        document.getElementById('newTestNotes').value = '';
                        await loadPcbTests(activePcbId);
                    } else {
                        const err = await response.json();
                        alert('Failed to add test: ' + (err.detail || 'Unknown error'));
                    }
                } catch (e) {
                    alert('Network error: ' + e.message);
                }
            }

            async function saveStatusAndActiveTests() {
                const newStatus = document.getElementById('pcbStatusSelect').value;

                try {
                    await fetch('/pcbs/' + activePcbId, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: newStatus })
                    });

                    const today = new Date();
                    for (const test of currentPcbTests) {
                        const testDate = new Date(test.test_date);
                        const diffDays = Math.floor((today - testDate) / (1000 * 60 * 60 * 24));
                        
                        if (diffDays <= 365) {
                            const resElem = document.getElementById('test_res_' + test.id);
                            const notesElem = document.getElementById('test_notes_' + test.id);
                            if (resElem && notesElem) {
                                await fetch('/pcbs/' + activePcbId + '/tests/' + test.id, {
                                    method: 'PATCH',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        result: resElem.value,
                                        notes: notesElem.value
                                    })
                                });
                            }
                        }
                    }

                    closeManageModal();
                    window.location.reload();
                } catch (e) {
                    alert('Error saving updates: ' + e.message);
                }
            }

            // --- Live Search & Pagination Engine ---
            let currentPage = 1;
            let pageSize = 10;
            let filteredRows = [];

            function getTableRows() {
                const tbody = document.querySelector(".table-responsive tbody");
                return Array.from(tbody ? tbody.querySelectorAll("tr") : []);
            }

            function applyTableFilterAndPagination() {
                const allRows = getTableRows();
                const query = (document.getElementById("tableSearchInput") ? document.getElementById("tableSearchInput").value : "").trim().toLowerCase();
                
                // Normalizasyon: "in diagnosis" <-> "in_diagnosis"
                const cleanQuery = query.replace(/\s+/g, "_");

                filteredRows = allRows.filter(row => {
                    if (!query) return true;
                    const text = row.innerText.toLowerCase();
                    const textUnderscore = text.replace(/\s+/g, "_");
                    
                    // Doğrudan metin, alt çizgili metin veya archive prefix kontrolü
                    if (text.includes(query) || textUnderscore.includes(cleanQuery)) return true;
                    if (query.length >= 2 && ("archived".startsWith(query) || "archive".startsWith(query)) && text.includes("archived")) {
                        return true;
                    }
                    return false;
                });

                const totalItems = filteredRows.length;
                const effectivePageSize = pageSize === "all" ? (totalItems || 1) : parseInt(pageSize, 10);
                const totalPages = Math.max(1, Math.ceil(totalItems / effectivePageSize));

                if (currentPage > totalPages) currentPage = totalPages;
                if (currentPage < 1) currentPage = 1;

                const startIdx = (currentPage - 1) * effectivePageSize;
                const endIdx = pageSize === "all" ? totalItems : startIdx + effectivePageSize;

                allRows.forEach(row => { row.style.display = "none"; });
                filteredRows.slice(startIdx, endIdx).forEach(row => { row.style.display = ""; });

                // Sayaç ve sayfa göstergesi
                const counter = document.getElementById("tableCounter");
                if (counter) {
                    if (totalItems === 0) {
                        counter.innerText = query ? `No matching boards found for "${query}"` : "0 boards";
                    } else {
                        counter.innerText = `Showing ${Math.min(startIdx + 1, totalItems)}-${Math.min(endIdx, totalItems)} of ${totalItems} board${totalItems === 1 ? "" : "s"}`;
                    }
                }

                const indicator = document.getElementById("pageIndicator");
                if (indicator) indicator.innerText = `Page ${currentPage} of ${totalPages}`;

                const btnPrev = document.getElementById("btnPrevPage");
                if (btnPrev) {
                    btnPrev.disabled = currentPage <= 1;
                    btnPrev.style.opacity = currentPage <= 1 ? "0.5" : "1";
                    btnPrev.style.cursor = currentPage <= 1 ? "not-allowed" : "pointer";
                }

                const btnNext = document.getElementById("btnNextPage");
                if (btnNext) {
                    btnNext.disabled = currentPage >= totalPages;
                    btnNext.style.opacity = currentPage >= totalPages ? "0.5" : "1";
                    btnNext.style.cursor = currentPage >= totalPages ? "not-allowed" : "pointer";
                }
            }

            function onSearchChange(val) {
                currentPage = 1;
                applyTableFilterAndPagination();
            }

            function changePageSize(val) {
                pageSize = val;
                currentPage = 1;
                applyTableFilterAndPagination();
            }

            function prevPage() {
                if (currentPage > 1) {
                    currentPage--;
                    applyTableFilterAndPagination();
                }
            }

            function nextPage() {
                const effectivePageSize = pageSize === "all" ? filteredRows.length : parseInt(pageSize, 10);
                const totalPages = Math.ceil(filteredRows.length / effectivePageSize);
                if (currentPage < totalPages) {
                    currentPage++;
                    applyTableFilterAndPagination();
                }
            }

            // Sayfa yüklendiğinde otomatik başlat
            window.addEventListener("DOMContentLoaded", () => {
                applyTableFilterAndPagination();
            });
            setTimeout(applyTableFilterAndPagination, 100);
        </script>
    </body>
    </html>
    """

    html_content = html_head_and_body + js_script
    return HTMLResponse(content=html_content)


@app.get("/", tags=["General"])
def root():
    return {"message": "GreenUpPCB LIS API is operational"}
