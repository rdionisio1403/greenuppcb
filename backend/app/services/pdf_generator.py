import os
from datetime import datetime

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
)
from PIL import Image as PILImage


UPLOAD_DIR = "/opt/greenupcb/backend/uploads"
REPORTS_DIR = os.path.join(UPLOAD_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(
    TTFont("DejaVuSans", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
)
pdfmetrics.registerFont(
    TTFont("DejaVuSans-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
)


def safe(value, default="-"):
    if value is None or str(value).strip() == "":
        return default
    return str(value)


def format_date(value):
    if value is None:
        return "-"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


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
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="DejaVuSans-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=5,
    )

    section_title = ParagraphStyle(
        "SecTitle",
        parent=styles["Normal"],
        fontName="DejaVuSans-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=8,
        spaceAfter=6,
    )

    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName="DejaVuSans",
        fontSize=8.5,
        leading=11.5,
    )

    cell_bold = ParagraphStyle(
        "CellB",
        parent=styles["Normal"],
        fontName="DejaVuSans-Bold",
        fontSize=8.5,
        leading=11.5,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontName="DejaVuSans",
        fontSize=7.5,
        leading=10,
    )

    header_white = ParagraphStyle(
        "HeaderW",
        parent=styles["Normal"],
        fontName="DejaVuSans-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white,
    )

    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        fontName="DejaVuSans-Bold",
        fontSize=8,
        alignment=1,
        textColor=colors.HexColor("#1e293b"),
    )

    empty_style = ParagraphStyle(
        "Empty",
        parent=styles["Normal"],
        fontName="DejaVuSans",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )

    story = []

    # ============================================================
    # TITLE
    # ============================================================

    story.append(
        Paragraph(
            "GreenUp PCB — Technical Inspection & Service Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"<font color='#64748b'>"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} "
            f"| Tracking Ref: {safe(pcb_data.get('internal_reference'))}"
            f"</font>",
            cell_style,
        )
    )

    story.append(Spacer(1, 12))

    # ============================================================
    # PCB INFORMATION
    # ============================================================

    story.append(Paragraph("PCB Information", section_title))

    info_data = [
        [
            Paragraph("PCB ID", cell_bold),
            Paragraph(safe(pcb_data.get("id")), cell_style),
            Paragraph("Status", cell_bold),
            Paragraph(safe(pcb_data.get("status")).upper(), cell_style),
        ],
        [
            Paragraph("Internal Reference", cell_bold),
            Paragraph(safe(pcb_data.get("internal_reference")), cell_style),
            Paragraph("Customer", cell_bold),
            Paragraph(safe(pcb_data.get("customer_name")), cell_style),
        ],
        [
            Paragraph("Equipment", cell_bold),
            Paragraph(safe(pcb_data.get("equipment")), cell_style),
            Paragraph("Manufacturer", cell_bold),
            Paragraph(safe(pcb_data.get("manufacturer")), cell_style),
        ],
        [
            Paragraph("PCB Model", cell_bold),
            Paragraph(safe(pcb_data.get("pcb_model")), cell_style),
            Paragraph("Serial Number", cell_bold),
            Paragraph(safe(pcb_data.get("serial_number")), cell_style),
        ],
        [
            Paragraph("Date Received", cell_bold),
            Paragraph(format_date(pcb_data.get("date_received")), cell_style),
            Paragraph("Created At", cell_bold),
            Paragraph(safe(pcb_data.get("created_at")), cell_style),
        ],
        [
            Paragraph("Reported Failure", cell_bold),
            Paragraph(safe(pcb_data.get("failure_description")), cell_style),
            Paragraph("", cell_bold),
            Paragraph("", cell_style),
        ],
    ]

    t_info = Table(
        info_data,
        colWidths=[90, 171.5, 90, 171.5],
        repeatRows=0,
    )

    t_info.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#f8fafc"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#cbd5e1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#e2e8f0"),
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(t_info)
    story.append(Spacer(1, 12))

    # ============================================================
    # DIAGNOSIS HISTORY
    # ============================================================

    story.append(Paragraph("Diagnosis History", section_title))

    diagnoses = pcb_data.get("diagnoses", [])

    if diagnoses:
        diagnosis_data = [
            [
                Paragraph("#", header_white),
                Paragraph("Date", header_white),
                Paragraph("Technician", header_white),
                Paragraph("Fault Found", header_white),
                Paragraph("Recommended Action", header_white),
            ]
        ]

        for index, diagnosis in enumerate(diagnoses, start=1):
            diagnosis_data.append(
                [
                    Paragraph(str(index), cell_style),
                    Paragraph(format_date(diagnosis.get("date")), cell_style),
                    Paragraph(safe(diagnosis.get("technician")), cell_style),
                    Paragraph(safe(diagnosis.get("fault_found")), cell_style),
                    Paragraph(
                        safe(diagnosis.get("recommended_action")),
                        cell_style,
                    ),
                ]
            )

        t_diag = Table(
            diagnosis_data,
            colWidths=[25, 65, 80, 180, 173],
            repeatRows=1,
        )

        t_diag.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#0f172a"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        1,
                        colors.HexColor("#cbd5e1"),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#e2e8f0"),
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(t_diag)
    else:
        story.append(
            Paragraph("No diagnosis records have been recorded.", empty_style)
        )

    story.append(Spacer(1, 12))

    # ============================================================
    # REPAIR HISTORY
    # ============================================================

    story.append(Paragraph("Repair History", section_title))

    repairs = pcb_data.get("repairs", [])

    if repairs:
        repair_data = [
            [
                Paragraph("#", header_white),
                Paragraph("Date", header_white),
                Paragraph("Technician", header_white),
                Paragraph("Actions Taken", header_white),
                Paragraph("Components Replaced", header_white),
            ]
        ]

        for index, repair in enumerate(repairs, start=1):
            repair_data.append(
                [
                    Paragraph(str(index), cell_style),
                    Paragraph(format_date(repair.get("date")), cell_style),
                    Paragraph(safe(repair.get("technician")), cell_style),
                    Paragraph(
                        safe(repair.get("actions_taken")),
                        cell_style,
                    ),
                    Paragraph(
                        safe(repair.get("components_replaced")),
                        cell_style,
                    ),
                ]
            )

        t_repair = Table(
            repair_data,
            colWidths=[25, 65, 80, 205, 133],
            repeatRows=1,
        )

        t_repair.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#0f172a"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        1,
                        colors.HexColor("#cbd5e1"),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#e2e8f0"),
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(t_repair)
    else:
        story.append(
            Paragraph("No repair records have been recorded.", empty_style)
        )

    story.append(Spacer(1, 12))

    # ============================================================
    # TEST HISTORY
    # ============================================================

    story.append(Paragraph("Test History", section_title))

    tests = pcb_data.get("tests", [])

    if tests:
        test_data = [
            [
                Paragraph("#", header_white),
                Paragraph("Date", header_white),
                Paragraph("Tester", header_white),
                Paragraph("Test Type", header_white),
                Paragraph("Result", header_white),
                Paragraph("Notes", header_white),
            ]
        ]

        for index, test in enumerate(tests, start=1):
            test_data.append(
                [
                    Paragraph(str(index), cell_style),
                    Paragraph(format_date(test.get("date")), cell_style),
                    Paragraph(safe(test.get("tester")), cell_style),
                    Paragraph(safe(test.get("test_type")), cell_style),
                    Paragraph(
                        f"<b>{safe(test.get('result'))}</b>",
                        cell_style,
                    ),
                    Paragraph(safe(test.get("notes")), cell_style),
                ]
            )

        t_test = Table(
            test_data,
            colWidths=[25, 65, 75, 90, 65, 203],
            repeatRows=1,
        )

        t_test.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#0f172a"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        1,
                        colors.HexColor("#cbd5e1"),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#e2e8f0"),
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(t_test)
    else:
        story.append(
            Paragraph("No test records have been recorded.", empty_style)
        )

    story.append(Spacer(1, 12))

    # ============================================================
    # EVIDENCE / IMAGES
    # ============================================================

    if images_list:
        story.append(
            Paragraph(
                "Inspection & Verification Evidence",
                section_title,
            )
        )

        grid_items = []

        for im in images_list:
            clean_filename = os.path.basename(
                safe(im.get("path"), "")
            )

            if not clean_filename:
                continue

            full_path = os.path.join(UPLOAD_DIR, clean_filename)

            if not os.path.exists(full_path):
                continue

            display_path = full_path
            temp_jpg = None

            try:
                if full_path.lower().endswith(".webp"):
                    temp_jpg = os.path.join(
                        REPORTS_DIR,
                        f"temp_{clean_filename}.jpg",
                    )

                    with PILImage.open(full_path) as pimg:
                        pimg.convert("RGB").save(
                            temp_jpg,
                            "JPEG",
                            quality=75,
                        )

                    display_path = temp_jpg

                pil_img = PILImage.open(display_path)
                img_width, img_height = pil_img.size
                pil_img.close()

                max_width = 235
                max_height = 145

                ratio = min(
                    max_width / img_width,
                    max_height / img_height,
                )

                final_width = img_width * ratio
                final_height = img_height * ratio

                rl_img = RLImage(
                    display_path,
                    width=final_width,
                    height=final_height,
                )

                category = safe(im.get("category")).upper()
                technician = safe(im.get("technician"))

                caption = (
                    f"<b>[{category}]</b><br/>"
                    f"Technician: {technician}"
                )

                card = [
                    rl_img,
                    Paragraph(caption, badge_style),
                ]

                grid_items.append(card)

            except Exception:
                continue

        grid_rows = []

        for i in range(0, len(grid_items), 2):
            row = grid_items[i:i + 2]

            if len(row) == 1:
                row.append("")

            grid_rows.append(row)

        if grid_rows:
            t_grid = Table(
                grid_rows,
                colWidths=[261.5, 261.5],
            )

            t_grid.setStyle(
                TableStyle(
                    [
                        (
                            "ALIGN",
                            (0, 0),
                            (-1, -1),
                            "CENTER",
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                    ]
                )
            )

            story.append(t_grid)
        else:
            story.append(
                Paragraph(
                    "Image records exist, but no image files were found on disk.",
                    empty_style,
                )
            )
    else:
        story.append(
            Paragraph(
                "No inspection images have been recorded.",
                empty_style,
            )
        )

    # ============================================================
    # BUILD PDF
    # ============================================================

    doc.build(story)

    return f"/uploads/reports/{filename}"
