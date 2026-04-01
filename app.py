from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Global mock database
SYSTEM_INVENTORY = [
    {"id": "FC-001", "category": "Fuel Consumption", "name": "Diesel (Liters)", "system_qty": 500},
    {"id": "TV-001", "category": "Transport Vehicle", "name": "Ambulance Tires", "system_qty": 8},
    {"id": "MED-042", "category": "Medicines", "name": "Paracetamol 500mg (Box)", "system_qty": 120},
    {"id": "EMP-001", "category": "Emergency Supplies", "name": "Canned Goods (Box)", "system_qty": 50},
    {"id": "VET-011", "category": "Veterinary Supplies", "name": "Anti-Rabies Vaccine (Vial)", "system_qty": 15}
]

# Category Metadata for the menu
AUDIT_CATEGORIES = [
    {"name": "Fuel Consumption", "icon": "⛽", "desc": "Audit fuel reserves and usage logs."},
    {"name": "Transport Vehicle", "icon": "🚑", "desc": "Audit vehicle parts, tires, and maintenance."},
    {"name": "Medicines", "icon": "💊", "desc": "Audit pharmaceutical stocks and expiration dates."},
    {"name": "Emergency Supplies", "icon": "🔦", "desc": "Audit relief goods, water, and rescue equipment."},
    {"name": "Veterinary Supplies", "icon": "🐕", "desc": "Audit animal vaccines and veterinary medicines."}
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    return render_template('index.html')

@app.route('/audit')
def audit_categories():
    return render_template('audit_categories.html', categories=AUDIT_CATEGORIES)

@app.route('/audit/<category_name>', methods=['GET', 'POST'])
def audit_form(category_name):
    filtered_items = [item for item in SYSTEM_INVENTORY if item['category'] == category_name]

    if request.method == 'POST':
        return render_template('audit_form.html', category_name=category_name, items=filtered_items, success=True)

    return render_template('audit_form.html', category_name=category_name, items=filtered_items)

@app.route('/history')
def history():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)