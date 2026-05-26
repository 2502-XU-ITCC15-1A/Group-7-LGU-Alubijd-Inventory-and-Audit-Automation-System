import calendar
import datetime

from flask import Blueprint, session, request, redirect, url_for, make_response
from services.audit_service import ensure_audit_log_table
from services.inventory_service import get_items_by_category_name
from extensions import mysql
from routes.auth import login_required
from pdf_generator import generate_physical_count_pdf

pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.route("/audit/<category_name>/download-pdf", methods=["POST"])
@login_required
def download_pdf(category_name):
    form = request.form

    as_of_date        = form.get("as_of_date", datetime.date.today().strftime("%B %d, %Y"))
    accountable_person = form.get("accountable_person", "")
    position          = form.get("position", "")
    department        = form.get("department", "")

    items = _collect_pdf_items_from_form(form)

    pdf_buffer = generate_physical_count_pdf(
        category_name=category_name,
        as_of_date=as_of_date,
        accountable_person=accountable_person,
        position=position,
        department=department,
        items=items,
    )

    return _make_pdf_response(pdf_buffer, f"Physical_Count_{category_name.replace(' ', '_')}.pdf")


@pdf_bp.route("/api/generate_pdf_monthly")
@login_required
def generate_pdf_monthly():
    category_name    = request.args.get("category")
    subcategory_name = request.args.get("subcategory")
    # support either single month/day or a start/end month range
    month  = request.args.get("month")
    year   = request.args.get("year")
    day    = request.args.get("day")

    start_month = request.args.get("start_month")
    start_year = request.args.get("start_year")
    end_month = request.args.get("end_month")
    end_year = request.args.get("end_year")

    # also accept explicit ISO date range parameters: start_date and end_date (YYYY-MM-DD)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    accountable_person = request.args.get("person",        "First Middle Last Name")
    position           = request.args.get("position",      "Position Title")
    department         = request.args.get("dept",          "Department Name")
    certified_by       = request.args.get("certified",     "First Middle Last Name")
    certified_role     = request.args.get("certified_role","Position Title")
    approved_by        = request.args.get("approved",      "First Middle Last Name")
    approved_role      = request.args.get("approved_role", "Position Title")

    cat, db_items = get_items_by_category_name(mysql, category_name)
    if cat is None:
        return "Category not found", 404

    # If explicit ISO start/end provided, use them
    if start_date_str and end_date_str:
        try:
            start_dt = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_dt = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except Exception:
            return "Invalid start/end date format", 400

        if start_dt > end_dt:
            # swap
            start_dt, end_dt = end_dt, start_dt

        db_items = _filter_items_by_range(category_name, subcategory_name, start_dt, end_dt)
        if db_items is None:
            return "Category not found", 404

        as_of_date = f"{start_dt.strftime('%b %d, %Y')} - {end_dt.strftime('%b %d, %Y')}"
        filename_range = f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
    # If a start/end month provided, use range filter
    elif start_month and end_month:
        try:
            sm = int(start_month); sy = int(start_year or datetime.date.today().year)
            em = int(end_month); ey = int(end_year or datetime.date.today().year)
            start_dt = datetime.date(sy, sm, 1)
            last_day = calendar.monthrange(ey, em)[1]
            end_dt = datetime.date(ey, em, last_day)
        except Exception:
            return "Invalid date range", 400

        db_items = _filter_items_by_range(category_name, subcategory_name, start_dt, end_dt)
        if db_items is None:
            return "Category not found", 404

        start_name = calendar.month_name[sm]
        end_name = calendar.month_name[em]
        if sy == ey:
            as_of_date = f"{start_name} - {end_name} {sy}"
        else:
            as_of_date = f"{start_name} {sy} - {end_name} {ey}"
        filename_range = f"{start_name}-{end_name}_{ey}"
    else:
        # single month / optional day
        m = int(month or datetime.date.today().month)
        y = int(year or datetime.date.today().year)
        db_items = _filter_items_by_date(category_name, subcategory_name, m, y, day)
        if db_items is None:
            return "Category not found", 404

        month_name = calendar.month_name[m]
        as_of_date = f"{month_name} {day + ', ' if day else ''}{y}"

    pdf_items = [_map_db_item_to_pdf(it) for it in db_items]

    pdf_buffer = generate_physical_count_pdf(
        category_name=category_name,
        as_of_date=as_of_date,
        accountable_person=accountable_person,
        position=position,
        department=department,
        items=pdf_items,
        certified_by=certified_by,
        certified_role=certified_role,
        approved_by=approved_by,
        approved_role=approved_role,
    )

    day_str  = f"_{day}" if day else ""
    # prefer filename_range when created from any range (ISO or month range)
    if (start_date_str and end_date_str) or (start_month and end_month):
        filename = f"Audit_{category_name.replace(' ', '_')}_{filename_range}.pdf"
    else:
        filename = f"Audit_{category_name.replace(' ', '_')}{day_str}_{month_name}_{y}.pdf"
    return _make_pdf_response(pdf_buffer, filename)


def _filter_items_by_range(category_name, subcategory_name, start_date, end_date):
    """Filter items by a date range (inclusive) using date_created or date_updated."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    cat = cur.fetchone()
    if not cat:
        return None

    query = """
        SELECT i.*, c.name AS category_name, s.name AS subcategory_name
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.id
        JOIN subcategories s ON i.subcategory_id = s.id
        WHERE i.category_id = %s
    """
    params = [cat["id"]]

    if subcategory_name:
        query += " AND s.name = %s"
        params.append(subcategory_name)

    query += """
        AND (
            (i.date_created BETWEEN %s AND %s)
            OR (i.date_updated BETWEEN %s AND %s)
        )
    """
    params.extend([start_date, end_date, start_date, end_date])

    cur.execute(query, tuple(params))
    return cur.fetchall()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect_pdf_items_from_form(form):
    keys = ["pdf_article[]", "pdf_desc[]", "pdf_propno[]", "pdf_unit[]",
            "pdf_unitval[]", "pdf_qtycard[]", "pdf_qtyphys[]", "pdf_remarks[]"]
    lists = [form.getlist(k) for k in keys]
    length = len(lists[0])

    return [
        {
            "article":      lists[0][i] if i < len(lists[0]) else "",
            "description":  lists[1][i] if i < len(lists[1]) else "",
            "property_no":  lists[2][i] if i < len(lists[2]) else "",
            "unit_measure": lists[3][i] if i < len(lists[3]) else "",
            "unit_value":   lists[4][i] if i < len(lists[4]) else "",
            "qty_card":     lists[5][i] if i < len(lists[5]) else "",
            "qty_physical": lists[6][i] if i < len(lists[6]) else "",
            "remarks":      lists[7][i] if i < len(lists[7]) else "",
        }
        for i in range(length)
    ]


def _filter_items_by_date(category_name, subcategory_name, month, year, day):
    """Run the date-filtered inventory query and return rows."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    cat = cur.fetchone()
    if not cat:
        return None

    query = """
        SELECT i.*, c.name AS category_name, s.name AS subcategory_name
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.id
        JOIN subcategories s ON i.subcategory_id = s.id
        WHERE i.category_id = %s
    """
    params = [cat["id"]]

    if subcategory_name:
        query += " AND s.name = %s"
        params.append(subcategory_name)

    if day:
        query += """
            AND (
                (DAY(i.date_created) = %s AND MONTH(i.date_created) = %s AND YEAR(i.date_created) = %s)
                OR
                (DAY(i.date_updated) = %s AND MONTH(i.date_updated) = %s AND YEAR(i.date_updated) = %s)
            )
        """
        params.extend([int(day), month, year, int(day), month, year])
    else:
        query += """
            AND (
                (MONTH(i.date_created) = %s AND YEAR(i.date_created) = %s)
                OR
                (MONTH(i.date_updated) = %s AND YEAR(i.date_updated) = %s)
            )
        """
        params.extend([month, year, month, year])

    cur.execute(query, tuple(params))
    return cur.fetchall()


def _map_db_item_to_pdf(item):
    return {
        "article":      item["article"] or item["subcategory_name"],
        "description":  item["name"],
        "property_no":  item["stock_number"] or "",
        "unit_measure": item["unit_of_measure"] or "",
        "unit_value":   item["unit_value"] or 0,
        "qty_card":     item["quantity"],
        "qty_physical": item["on_hand_per_count"] or 0,
        "remarks":      item["remarks"] or "",
    }


def _make_pdf_response(pdf_buffer, filename):
    response = make_response(pdf_buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
