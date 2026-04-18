import os, datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash
from functools import wraps

from pdf_generator import generate_physical_count_pdf

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'alias_db')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

SYSTEM_INVENTORY = [
    {"id": "FC-001",  "category": "Fuel Consumption",   "name": "Diesel (Liters)",            "system_qty": 500},
    {"id": "TV-001",  "category": "Transport Vehicle",  "name": "Ambulance Tires",            "system_qty": 8},
    {"id": "MED-042", "category": "Medicines",          "name": "Paracetamol 500mg (Box)",    "system_qty": 120},
    {"id": "EMP-001", "category": "Emergency Supplies", "name": "Canned Goods (Box)",         "system_qty": 50},
    {"id": "VET-011", "category": "Veterinary Supplies","name": "Anti-Rabies Vaccine (Vial)", "system_qty": 15},
]

AUDIT_CATEGORIES = [
    {"name": "Fuel Consumption",   "icon": "⛽", "desc": "Audit fuel reserves and usage logs."},
    {"name": "Transport Vehicle",  "icon": "🚑", "desc": "Audit vehicle parts, tires, and maintenance."},
    {"name": "Medicines",          "icon": "💊", "desc": "Audit pharmaceutical stocks and expiration dates."},
    {"name": "Emergency Supplies", "icon": "🔦", "desc": "Audit relief goods, water, and rescue equipment."},
    {"name": "Property, Plant and Equipment ICT", "icon": "", "desc": "Audit physical plant and equipment."}
]

# ---------------- DECORATORS ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user and user['password'] == password:
            session.clear()
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))

        flash("Login failed. Wrong username or password.")
        return redirect(url_for('login'))

    return render_template('login.html')


# ---------------- LOGOUT ----------------
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- HOME ----------------
@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/inventory')
@login_required
def inventory():
    return render_template('index.html')

@app.route('/audit')
@login_required
def audit_categories():
    return render_template('audit_categories.html', categories=AUDIT_CATEGORIES)

@app.route('/audit/<category_name>', methods=['GET', 'POST'])
@login_required
def audit_form(category_name):
    filtered_items = [item for item in SYSTEM_INVENTORY if item['category'] == category_name]

    if request.method == 'POST':
        return render_template('audit_form.html',
                               category_name=category_name,
                               items=filtered_items,
                               success=True)

    return render_template('audit_form.html',
                           category_name=category_name,
                           items=filtered_items)

@app.route('/audit/<category_name>/download-pdf', methods=['POST'])
@login_required
def download_pdf(category_name):
    form = request.form

    as_of_date        = form.get('as_of_date', datetime.date.today().strftime('%B %d, %Y'))
    accountable_person = form.get('accountable_person', 'DOLLYN JEAN A. SABELLINA')
    position          = form.get('position', 'MUNICIPAL ACCOUNTANT')
    department        = form.get('department', 'ACCOUNTING')

    articles   = form.getlist('pdf_article[]')
    descs      = form.getlist('pdf_desc[]')
    prop_nos   = form.getlist('pdf_propno[]')
    units      = form.getlist('pdf_unit[]')
    unit_vals  = form.getlist('pdf_unitval[]')
    qty_cards  = form.getlist('pdf_qtycard[]')
    qty_phys   = form.getlist('pdf_qtyphys[]')
    remarks_l  = form.getlist('pdf_remarks[]')

    items = []
    for i in range(len(articles)):
        items.append({
            'article':     articles[i]   if i < len(articles)  else '',
            'description': descs[i]      if i < len(descs)     else '',
            'property_no': prop_nos[i]   if i < len(prop_nos)  else '',
            'unit_measure': units[i]     if i < len(units)     else '',
            'unit_value':  unit_vals[i]  if i < len(unit_vals) else '',
            'qty_card':    qty_cards[i]  if i < len(qty_cards) else '',
            'qty_physical': qty_phys[i]  if i < len(qty_phys)  else '',
            'remarks':     remarks_l[i]  if i < len(remarks_l) else '',
        })

    pdf_buffer = generate_physical_count_pdf(
        category_name=category_name,
        as_of_date=as_of_date,
        accountable_person=accountable_person,
        position=position,
        department=department,
        items=items
    )

    safe_name = category_name.replace(' ', '_')
    filename  = f"Physical_Count_{safe_name}.pdf"

    response = make_response(pdf_buffer.read())
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@app.route('/history')
@login_required
def history():
    return render_template('history.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
