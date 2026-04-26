import io
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# colour palette
HEADER_BG   = colors.HexColor("#FFFFFF")   # column headers
ALT_ROW_BG  = colors.HexColor("#EBF0FA")   # alternating rows
SHORTAGE_FG = colors.HexColor("#CC0000")   # shortage values
BLACK       = colors.black
WHITE       = colors.white
LIGHT_GREY  = colors.HexColor("#D9D9D9")


# paragraph styles
def _styles():
    base = dict(fontName="Helvetica", leading=11)
    return {
        "title": ParagraphStyle("title",
            fontName="Helvetica-Bold", fontSize=11,
            alignment=TA_CENTER, leading=14, spaceAfter=1),
        "subtitle": ParagraphStyle("subtitle",
            fontName="Helvetica-Bold", fontSize=10,
            alignment=TA_CENTER, leading=13, spaceAfter=1),
        "date": ParagraphStyle("date",
            fontName="Helvetica", fontSize=9,
            alignment=TA_CENTER, leading=11, spaceAfter=6),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=8.5,
            alignment=TA_LEFT, leading=11),
        "cell": ParagraphStyle("cell",
            fontName="Helvetica", fontSize=7.5,
            alignment=TA_LEFT, leading=10),
        "cell_c": ParagraphStyle("cell_c",
            fontName="Helvetica", fontSize=7.5,
            alignment=TA_CENTER, leading=10),
        "cell_r": ParagraphStyle("cell_r",
            fontName="Helvetica", fontSize=7.5,
            alignment=TA_RIGHT, leading=10),
        "cell_red": ParagraphStyle("cell_red",
            fontName="Helvetica", fontSize=7.5,
            alignment=TA_RIGHT, leading=10, textColor=SHORTAGE_FG),
        "cell_red_c": ParagraphStyle("cell_red_c",
            fontName="Helvetica", fontSize=7.5,
            alignment=TA_CENTER, leading=10, textColor=SHORTAGE_FG),
        "hdr": ParagraphStyle("hdr",
            fontName="Helvetica-Bold", fontSize=7.5,
            alignment=TA_CENTER, leading=10, textColor=BLACK),
        "sig_label": ParagraphStyle("sig_label",
            fontName="Helvetica", fontSize=8,
            alignment=TA_CENTER, leading=11),
        "sig_name": ParagraphStyle("sig_name",
            fontName="Helvetica-Bold", fontSize=8.5,
            alignment=TA_CENTER, leading=12),
        "sig_role": ParagraphStyle("sig_role",
            fontName="Helvetica", fontSize=7.5,
            alignment=TA_CENTER, leading=10),
    }

# currency formatter
def _fmt(value):
    try:
        f = float(str(value).replace(",", ""))
        return f"{f:,.2f}"
    except (ValueError, TypeError):
        return str(value) if value else ""


# main generator
def generate_physical_count_pdf(
    category_name,
    as_of_date,
    accountable_person="",
    position="",
    department="",
    items=None,
    certified_by="",
    certified_role="GSO-Designate / Inventory Chair Committee",
    approved_by="",
    approved_role="Municipal Mayor",
):

    if items is None:
        items = []

    buf = io.BytesIO()
    S = _styles()

    page_w, page_h = landscape(A4)
    margin = 15 * mm

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story = []

    # Header
    story.append(Paragraph(
        "REPORT ON THE PHYSICAL COUNT OF PROPERTY, PLANT AND EQUIPMENT",
        S["title"]
    ))
    story.append(Paragraph(
        f"{category_name.upper()} EQUIPMENT",
        S["subtitle"]
    ))
    story.append(Paragraph(f"As of {as_of_date}", S["date"]))

    person_str = accountable_person or "_______________"
    pos_str    = position           or "_______________"
    dept_str   = department         or "_______________"
    story.append(Paragraph(
        f"For which &nbsp;<u><b>{person_str}</b></u>, &nbsp;"
        f"<u><b>{pos_str}</b></u>, &nbsp;"
        f"<u><b>{dept_str}</b></u>&nbsp; "
        f"is accountable, having assumed such accountability on ___________",
        S["body"]
    ))
    story.append(Spacer(1, 6))

    usable = page_w - 2 * margin
    col_w = [
        22 * mm,   # Article
        48 * mm,   # Description
        20 * mm,   # Property No.
        18 * mm,   # Unit Measure
        22 * mm,   # Unit Value
        18 * mm,   # Qty / Property Card
        18 * mm,   # Qty / Physical Count
        16 * mm,   # Shortage Qty
        22 * mm,   # Shortage Value
        usable - 204 * mm,
    ]

    # Table header rows
    def H(txt):
        return Paragraph(txt, S["hdr"])

    header_row1 = [
        H("Article"),
        H("Description"),
        H("Property No."),
        H("Unit\nMeasure"),
        H("Unit Value"),
        H("Quantity per\nProperty Card"),
        H("Quantity per\nPhysical Count"),
        H("Shortage /\nOverage"),
        "",
        H("Remarks"),
    ]
    header_row2 = [
        "", "", "", "", "", "", "",
        H("Quantity"),
        H("Value"),
        "",
    ]

    # Data rows
    data_rows = []
    for idx, it in enumerate(items):
        try:
            qty_card  = int(float(str(it.get("qty_card", 0) or 0)))
            qty_phys  = int(float(str(it.get("qty_physical", 0) or 0)))
            unit_val  = float(str(it.get("unit_value", 0) or 0).replace(",", ""))
        except (ValueError, TypeError):
            qty_card, qty_phys, unit_val = 0, 0, 0.0

        shortage_qty = qty_phys - qty_card
        shortage_val = shortage_qty * unit_val

        s_qty_style = S["cell_red_c"] if shortage_qty < 0 else S["cell_c"]
        s_val_style = S["cell_red"]   if shortage_val < 0 else S["cell_r"]

        row = [
            Paragraph(str(it.get("article", "") or ""),        S["cell"]),
            Paragraph(str(it.get("description", "") or ""),    S["cell"]),
            Paragraph(str(it.get("property_no", "") or ""),    S["cell_c"]),
            Paragraph(str(it.get("unit_measure", "") or ""),   S["cell_c"]),
            Paragraph(_fmt(unit_val),                           S["cell_r"]),
            Paragraph(str(qty_card),                            S["cell_c"]),
            Paragraph(str(qty_phys),                            S["cell_c"]),
            Paragraph(str(shortage_qty),                        s_qty_style),
            Paragraph(_fmt(shortage_val),                       s_val_style),
            Paragraph(str(it.get("remarks", "") or ""),         S["cell"]),
        ]
        data_rows.append(row)

    all_rows = [header_row1, header_row2] + data_rows

    tbl = Table(all_rows, colWidths=col_w, repeatRows=2)

    # Table styling
    n_data = len(data_rows)
    style_cmds = [
        ("BOX",        (0, 0), (-1, -1), 0.8, BLACK),
        ("INNERGRID",  (0, 0), (-1, -1), 0.4, colors.HexColor("#AAAAAA")),

        ("BACKGROUND", (0, 0), (-1, 1),  HEADER_BG),

        ("SPAN",       (7, 0), (8, 0)),
        ("SPAN",       (9, 0), (9, 1)),
        *[("SPAN", (c, 0), (c, 1)) for c in range(7)],

        ("VALIGN",     (0, 0), (-1, 1),  "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 1),  4),
        ("BOTTOMPADDING", (0, 0), (-1, 1), 4),

        ("VALIGN",     (0, 2), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 2), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 2), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]

    for i in range(n_data):
        if i % 2 == 1:
            style_cmds.append(
                ("BACKGROUND", (0, 2 + i), (-1, 2 + i), ALT_ROW_BG)
            )

    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(Spacer(1, 10))

    # Signature block
    cert_name  = certified_by   or "________________________________"
    cert_role  = certified_role or "GSO-Designate / Inventory Chair Committee"
    appr_name  = approved_by    or "________________________________"
    appr_role  = approved_role  or "Municipal Mayor"

    def _sig_col(label, name, role_lines):
        lines = [
            Paragraph(label, S["sig_label"]),
            Spacer(1, 20),
            HRFlowable(width="80%", thickness=0.6, color=BLACK, spaceAfter=2),
            Paragraph(f"<b><u>{name}</u></b>", S["sig_name"]),
        ]
        for r in (role_lines if isinstance(role_lines, list) else [role_lines]):
            lines.append(Paragraph(r, S["sig_role"]))
        return lines

    sig_data = [[
        _sig_col("Certified Correct by:", cert_name, cert_role),
        _sig_col("Approved by:", appr_name, appr_role),
        [
            Paragraph("Verified by:", S["sig_label"]),
            Spacer(1, 20),
            HRFlowable(width="80%", thickness=0.6, color=BLACK, spaceAfter=2),
            Paragraph("COA Representative", S["sig_role"]),
        ],
    ]]

    sig_tbl = Table(sig_data, colWidths=[usable / 3] * 3)
    sig_tbl.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_tbl)

    doc.build(story)
    buf.seek(0)
    return buf