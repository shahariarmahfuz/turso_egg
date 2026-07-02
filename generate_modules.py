import os
import re

modules = {
    "Supplier": [
        ("Add Supplier", "add_supplier"),
        ("Manage Supplier", "manage_supplier"),
        ("Supplier Ledger", "supplier_ledger"),
        ("Supplier Due List", "supplier_due_list")
    ],
    "Purchase": [
        ("Add Purchase", "add_purchase"),
        ("Manage Purchase", "manage_purchase"),
        ("Purchase Report", "purchase_report"),
        ("Purchase Items Report", "purchase_items_report")
    ],
    "Purchase Return": [
        ("Add Purchase Return", "add_purchase_return"),
        ("Manage Purchase Return", "manage_purchase_return"),
        ("Purchase Return Report", "purchase_return_report")
    ],
    "Customer": [
        ("Add Customer", "add_customer"),
        ("Manage Customer", "manage_customer"),
        ("Customer Ledger", "customer_ledger"),
        ("Customer Due List", "customer_due_list")
    ],
    "Sale": [
        ("Add Sale", "add_sale"),
        ("Manage Sale", "manage_sale"),
        ("Sale Report", "sale_report"),
        ("Sale Item Report", "sale_item_report")
    ],
    "Sale Return": [
        ("Add Sale Return", "add_sale_return"),
        ("Manage Sale Return", "manage_sale_return"),
        ("Sale Return Report", "sale_return_report")
    ],
    "Customer Collection": [
        ("Collection", "collection"),
        ("Manage Collection", "manage_collection"),
        ("Collections Report", "collections_report")
    ],
    "Account Reports": [
        ("Expense Report", "expense_report"),
        ("Income Report", "income_report"),
        ("Bank Report", "bank_report"),
        ("Bank Statement", "bank_statement"),
        ("Cash Book", "cash_book")
    ]
}

icons = {
    "Supplier": "fa-truck",
    "Purchase": "fa-cart-shopping",
    "Purchase Return": "fa-undo",
    "Customer": "fa-users",
    "Sale": "fa-bag-shopping",
    "Sale Return": "fa-rotate-left",
    "Customer Collection": "fa-money-bill-wave",
    "Account Reports": "fa-chart-line"
}

blueprint_template = """from flask import Blueprint, render_template
from flask_login import login_required

{bp_name}_bp = Blueprint('{bp_name}', __name__, url_prefix='/{bp_name}')

{routes}
"""

route_template = """@login_required
@{bp_name}_bp.route('/{route}')
def {route}():
    return render_template('placeholder.html', title="{title}")
"""

app_py_file = '/workspaces/egg/app.py'

def to_snake(name):
    return name.replace(' ', '_').lower()

# 1. Create Blueprints
for module, items in modules.items():
    bp_name = to_snake(module)
    routes = ""
    for title, _ in items:
        route = to_snake(title)
        routes += route_template.format(bp_name=bp_name, route=route, title=title)
    
    with open(f'/workspaces/egg/{bp_name}.py', 'w') as f:
        f.write(blueprint_template.format(bp_name=bp_name, routes=routes))

# 2. Update app.py
with open(app_py_file, 'r') as f:
    app_content = f.read()

imports = []
registrations = []
for module in modules.keys():
    bp_name = to_snake(module)
    imports.append(f"    from {bp_name} import {bp_name}_bp")
    registrations.append(f"    app.register_blueprint({bp_name}_bp)")

import_str = "\n".join(imports)
reg_str = "\n".join(registrations)

if "from supplier import supplier_bp" not in app_content:
    new_code = f"{import_str}\n{reg_str}"
    target = "from expenses import expenses_bp\n    app.register_blueprint(expenses_bp)"
    app_content = app_content.replace(target, f"{target}\n\n{new_code}")
    with open(app_py_file, 'w') as f:
        f.write(app_content)

# 3. Create placeholder.html
placeholder_html = """{% extends "layout.html" %}
{% block content %}
<div class="d-sm-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0 text-gray-800">{{ title }}</h1>
</div>
<div class="card shadow mb-4">
    <div class="card-header py-3 bg-white">
        <h6 class="m-0 font-weight-bold text-primary">{{ title }}</h6>
    </div>
    <div class="card-body">
        <p>This is a placeholder page for the <strong>{{ title }}</strong> module.</p>
        <p>Future development will add functionality here.</p>
    </div>
</div>
{% endblock %}
"""
with open('/workspaces/egg/templates/placeholder.html', 'w') as f:
    f.write(placeholder_html)

# 4. Generate Sidebar
sidebar_html = """
        <!-- Sidebar -->
        <div class="bg-dark text-white border-end" id="sidebar-wrapper" style="overflow-y: auto;">
            <div class="sidebar-heading text-center py-4 fs-4 fw-bold border-bottom">
                <i class="fa-solid fa-building me-2"></i>BMS
            </div>
            
            <div class="accordion accordion-flush w-100" id="sidebarAccordion">
                <!-- Dashboard -->
                <div class="accordion-item bg-dark border-0">
                    <h2 class="accordion-header" id="headingDashboard">
                        <a href="{{ url_for('routes.dashboard') }}" class="accordion-button bg-dark text-white shadow-none {% if request.endpoint == 'routes.dashboard' %}active-menu{% endif %} d-flex align-items-center" style="padding: 1rem 1.25rem; text-decoration: none;">
                            <i class="fa-solid fa-gauge me-3" style="width: 20px;"></i>
                            <span>Dashboard</span>
                        </a>
                    </h2>
                </div>

                <!-- Cash Out -->
                <div class="accordion-item bg-dark border-0">
                    <h2 class="accordion-header" id="headingCashOut">
                        <button class="accordion-button bg-dark text-white shadow-none collapsed d-flex align-items-center" type="button" data-bs-toggle="collapse" data-bs-target="#collapseCashOut" aria-expanded="{% if 'expenses.' in request.endpoint %}true{% else %}false{% endif %}" aria-controls="collapseCashOut" style="padding: 1rem 1.25rem;">
                            <i class="fa-solid fa-money-bill-wave me-3" style="width: 20px;"></i>
                            <span>Cash Out</span>
                        </button>
                    </h2>
                    <div id="collapseCashOut" class="accordion-collapse collapse {% if 'expenses.' in request.endpoint %}show{% endif %}" aria-labelledby="headingCashOut" data-bs-parent="#sidebarAccordion">
                        <div class="accordion-body p-0">
                            <div class="list-group list-group-flush bg-dark">
                                <a href="#" class="list-group-item list-group-item-action bg-dark text-white-50 border-0 py-2 ps-5 disabled fw-bold" style="font-size: 0.85rem;">Add</a>
                                <a href="{{ url_for('expenses.add_expense_entry') }}" class="list-group-item list-group-item-action bg-dark text-white border-0 py-2 ps-5 {% if request.endpoint == 'expenses.add_expense_entry' %}active-menu{% endif %}"><i class="fa-solid fa-caret-right me-2 text-white-50"></i>Expense Entry</a>
                                <a href="{{ url_for('expenses.add_expense_head') }}" class="list-group-item list-group-item-action bg-dark text-white border-0 py-2 ps-5 {% if request.endpoint == 'expenses.add_expense_head' %}active-menu{% endif %}"><i class="fa-solid fa-caret-right me-2 text-white-50"></i>Add Head</a>
                                <a href="#" class="list-group-item list-group-item-action bg-dark text-white-50 border-0 py-2 ps-5 disabled fw-bold mt-2" style="font-size: 0.85rem;">Manage</a>
                                <a href="{{ url_for('expenses.manage_expense_head') }}" class="list-group-item list-group-item-action bg-dark text-white border-0 py-2 ps-5 {% if request.endpoint == 'expenses.manage_expense_head' %}active-menu{% endif %}"><i class="fa-solid fa-caret-right me-2 text-white-50"></i>Manage Head</a>
                                <a href="{{ url_for('expenses.manage_daily_expense') }}" class="list-group-item list-group-item-action bg-dark text-white border-0 py-2 ps-5 {% if request.endpoint == 'expenses.manage_daily_expense' %}active-menu{% endif %}"><i class="fa-solid fa-caret-right me-2 text-white-50"></i>Daily Expense</a>
                                <a href="{{ url_for('expenses.manage_daily_expense') }}" class="list-group-item list-group-item-action bg-dark text-white border-0 py-2 ps-5 {% if request.endpoint == 'expenses.manage_daily_expense' %}active-menu{% endif %}"><i class="fa-solid fa-caret-right me-2 text-white-50"></i>Manage Daily Expense</a>
                            </div>
                        </div>
                    </div>
                </div>
"""

for module, items in modules.items():
    bp_name = to_snake(module)
    icon = icons[module]
    collapse_id = f"collapse{bp_name}"
    heading_id = f"heading{bp_name}"
    
    sidebar_html += f"""
                <!-- {module} -->
                <div class="accordion-item bg-dark border-0">
                    <h2 class="accordion-header" id="{heading_id}">
                        <button class="accordion-button bg-dark text-white shadow-none collapsed d-flex align-items-center" type="button" data-bs-toggle="collapse" data-bs-target="#{collapse_id}" aria-expanded="{{% if '{bp_name}.' in request.endpoint %}}true{{% else %}}false{{% endif %}}" aria-controls="{collapse_id}" style="padding: 1rem 1.25rem;">
                            <i class="fa-solid {icon} me-3" style="width: 20px;"></i>
                            <span>{module}</span>
                        </button>
                    </h2>
                    <div id="{collapse_id}" class="accordion-collapse collapse {{% if '{bp_name}.' in request.endpoint %}}show{{% endif %}}" aria-labelledby="{heading_id}" data-bs-parent="#sidebarAccordion">
                        <div class="accordion-body p-0">
                            <div class="list-group list-group-flush bg-dark">
"""
    for title, _ in items:
        route = to_snake(title)
        endpoint = f"{bp_name}.{route}"
        sidebar_html += f"""                                <a href="{{{{ url_for('{endpoint}') }}}}" class="list-group-item list-group-item-action bg-dark text-white border-0 py-2 ps-5 {{{{ 'active-menu' if request.endpoint == '{endpoint}' else '' }}}}"><i class="fa-solid fa-caret-right me-2 text-white-50"></i>{title}</a>\n"""
        
    sidebar_html += """                            </div>
                        </div>
                    </div>
                </div>
"""

sidebar_html += """
            </div>
        </div>
        <!-- /#sidebar-wrapper -->
"""

with open('/workspaces/egg/templates/layout.html', 'r') as f:
    layout_content = f.read()

layout_content = re.sub(r'<!-- Sidebar -->.*?<!-- /#sidebar-wrapper -->', sidebar_html, layout_content, flags=re.DOTALL)

with open('/workspaces/egg/templates/layout.html', 'w') as f:
    f.write(layout_content)

# 5. Append CSS styles for accordion
css_append = """
/* Sidebar Accordion Customizations */
.accordion-button::after {
    filter: invert(1);
    transform: scale(0.8);
}
.accordion-button:not(.collapsed) {
    background-color: #1a1e21;
    color: white;
    box-shadow: none;
}
.accordion-button:focus {
    box-shadow: none;
}
.accordion-item {
    background-color: transparent;
}
a.accordion-button::after {
    display: none;
}
.active-menu {
    background-color: #2b3035 !important;
    color: #0dcaf0 !important;
    font-weight: bold;
}
.active-menu i {
    color: #0dcaf0 !important;
}

#sidebar-wrapper {
    scrollbar-width: thin;
    scrollbar-color: #495057 #212529;
}
#sidebar-wrapper::-webkit-scrollbar {
    width: 6px;
}
#sidebar-wrapper::-webkit-scrollbar-track {
    background: #212529;
}
#sidebar-wrapper::-webkit-scrollbar-thumb {
    background-color: #495057;
    border-radius: 10px;
}
"""

with open('/workspaces/egg/static/css/style.css', 'a') as f:
    f.write(css_append)
