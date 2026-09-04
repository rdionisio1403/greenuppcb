import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage

UPLOAD_DIR = "/opt/greenupcb/backend/uploads"
REPORTS_DIR = os.path.join(UPLOAD_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_pcb_pdf(pcb_data: dict, images_list: list) -> str:
    pcb_id = pcb_data.get("id", 1)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_pcb_{pcb_id}_{timestamp_str}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    section_title = ParagraphStyle(
        "SecTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=5
    )
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.5, leading=11.5)
    cell_bold = ParagraphStyle("CellB", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11.5)
    
    # SADECE LACİVERT BAŞLIK İÇİN BEYAZ STİL
    header_white = ParagraphStyle(
        "HeaderW",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white
    )

    badge_style = ParagraphStyle(
        "Badge", 
        parent=styles["Normal"], 
        fontName="Helvetica-Bold", 
        fontSize=8, 
        alignment=1, 
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=3
    )

    story = []

    # Title Banner
    story.append(Paragraph("GreenUp PCB — Technical Inspection & Service Report", title_style))
    story.append(Paragraph(f"<font color='#64748b'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tracking Ref: {pcb_data.get('internal_reference', '-')}</font>", cell_style))
    story.append(Spacer(1, 12))

    # Core PCB Info
    info_data = [
        [Paragraph("PCB ID", cell_bold), Paragraph(str(pcb_data.get("id")), cell_style),
         Paragraph("Status", cell_bold), Paragraph(str(pcb_data.get("status", "-")).upper(), cell_style)],
        [Paragraph("Equipment", cell_bold), Paragraph(str(pcb_data.get("equipment", "-")), cell_style),
         Paragraph("Model", cell_bold), Paragraph(str(pcb_data.get("pcb_model", "-") or "-"), cell_style)],
        [Paragraph("Manufacturer", cell_bold), Paragraph(str(pcb_data.get("manufacturer", "-") or "-"), cell_style),
         Paragraph("Serial No", cell_bold), Paragraph(str(pcb_data.get("serial_number", "-") or "-"), cell_style)],
    ]
    t_info = Table(info_data, colWidths=[75, 186.5, 75, 186.5])
    t_info.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))

    # Lifecycle Operations Table
    story.append(Paragraph("Lifecycle Stage Summaries", section_title))
    lifecycle_data = [
        [Paragraph("Stage", header_white), Paragraph("Details / Action Taken", header_white), Paragraph("Result / Notes", header_white)],
        [Paragraph("Diagnosis", cell_bold), Paragraph(str(pcb_data.get("findings", "-") or "-"), cell_style), Paragraph(str(pcb_data.get("diag_notes", "-") or "-"), cell_style)],
        [Paragraph("Repair", cell_bold), Paragraph(str(pcb_data.get("action", "-") or "-"), cell_style), Paragraph(f"Components: {pcb_data.get('components_rep', '-') or '-'}", cell_style)],
        [Paragraph("Final Test", cell_bold), Paragraph(str(pcb_data.get("test_notes", "-") or "-"), cell_style), Paragraph(f"<b>{pcb_data.get('test_result', '-') or '-'}</b>", cell_style)],
    ]
    t_life = Table(lifecycle_data, colWidths=[80, 283, 160])
    t_life.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0f172a")),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t_life)
    story.append(Spacer(1, 14))

    # Evidence Gallery
    if images_list:
        story.append(Paragraph("Inspection & Verification Evidence", section_title))
        grid_items = []
        for im in images_list[:4]:
            clean_filename = os.path.basename(im.get("path", ""))
            full_path = os.path.join(UPLOAD_DIR, clean_filename)
            if os.path.exists(full_path):
                display_path = full_path
                temp_jpg = None
                try:
                    if full_path.lower().endswith(".webp"):
                        temp_jpg = os.path.join(REPORTS_DIR, f"temp_{clean_filename}.jpg")
                        with PILImage.open(full_path) as pimg:
                            pimg.convert("RGB").save(temp_jpg, "JPEG", quality=75)
                        display_path = temp_jpg

                    rl_img = RLImage(display_path, width=175, height=105)
                    card = [
                        rl_img,
                        Paragraph(f"<b>[{im.get('category', '').upper()}]</b>", badge_style)
                    ]
                    grid_items.append(card)
                except Exception:
                    pass

        grid_rows = []
        for i in range(0, len(grid_items), 2):
            row = grid_items[i:i+2]
            if len(row) == 1:
                row.append("")
            grid_rows.append(row)

        if grid_rows:
            t_grid = Table(grid_rows, colWidths=[261.5, 261.5])
            t_grid.setStyle(TableStyle([
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 3),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            story.append(t_grid)

    doc.build(story)
    return f"/uploads/reports/{filename}"
