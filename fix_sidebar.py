import os
import re

# 1. Update expenses.py
with open('/workspaces/egg/expenses.py', 'r') as f:
    exp_content = f.read()

exp_content = exp_content.replace("url_prefix='/cash_out'", "url_prefix='/expense'")
with open('/workspaces/egg/expenses.py', 'w') as f:
    f.write(exp_content)

# 2. Create cash_out.py
cash_out_content = """from flask import Blueprint, render_template
from flask_login import login_required

cash_out_bp = Blueprint('cash_out', __name__, url_prefix='/cash_out')

@login_required
@cash_out_bp.route('/add')
def add():
    return render_template('placeholder.html', title="Cash Out - Add")

@login_required
@cash_out_bp.route('/manage')
def manage():
    return render_template('placeholder.html', title="Cash Out - Manage")
"""
with open('/workspaces/egg/cash_out.py', 'w') as f:
    f.write(cash_out_content)

# 3. Update app.py
with open('/workspaces/egg/app.py', 'r') as f:
    app_content = f.read()

if "from cash_out import cash_out_bp" not in app_content:
    new_reg = "    from cash_out import cash_out_bp\n    app.register_blueprint(cash_out_bp)\n"
    app_content = app_content.replace("    from expenses import expenses_bp", f"{new_reg}    from expenses import expenses_bp")
    with open('/workspaces/egg/app.py', 'w') as f:
        f.write(app_content)

# 4. Update layout.html sidebar

modules = {
    "Cash Out": [
        ("Add", "cash_out.add"),
        ("Manage", "cash_out.manage")
    ],
    "Expense": [
        ("Expense Entry", "expenses.add_expense_entry"),
        ("Add Head", "expenses.add_expense_head"),
        ("Manage Head", "expenses.manage_expense_head"),
        ("Daily Expense", "expenses.manage_daily_expense"),
        ("Manage Daily Expense", "expenses.manage_daily_expense")
    ],
    "Supplier": [
        ("Add Supplier", "supplier.add_supplier"),
        ("Manage Supplier", "supplier.manage_supplier"),
        ("Supplier Ledger", "supplier.supplier_ledger"),
        ("Supplier Due List", "supplier.supplier_due_list")
    ],
    "Purchase": [
        ("Add Purchase", "purchase.add_purchase"),
        ("Manage Purchase", "purchase.manage_purchase"),
        ("Purchase Report", "purchase.purchase_report"),
        ("Purchase Items Report", "purchase.purchase_items_report")
    ],
    "Purchase Return": [
        ("Add Purchase Return", "purchase_return.add_purchase_return"),
        ("Manage Purchase Return", "purchase_return.manage_purchase_return"),
        ("Purchase Return Report", "purchase_return.purchase_return_report")
    ],
    "Customer": [
        ("Add Customer", "customer.add_customer"),
        ("Manage Customer", "customer.manage_customer"),
        ("Customer Ledger", "customer.customer_ledger"),
        ("Customer Due List", "customer.customer_due_list")
    ],
    "Sale": [
        ("Add Sale", "sale.add_sale"),
        ("Manage Sale", "sale.manage_sale"),
        ("Sale Report", "sale.sale_report"),
        ("Sale Item Report", "sale.sale_item_report")
    ],
    "Sale Return": [
        ("Add Sale Return", "sale_return.add_sale_return"),
        ("Manage Sale Return", "sale_return.manage_sale_return"),
        ("Sale Return Report", "sale_return.sale_return_report")
    ],
    "Customer Collection": [
        ("Collection", "customer_collection.collection"),
        ("Manage Collection", "customer_collection.manage_collection"),
        ("Collections Report", "customer_collection.collections_report")
    ],
    "Account Reports": [
        ("Expense Report", "account_reports.expense_report"),
        ("Income Report", "account_reports.income_report"),
        ("Bank Report", "account_reports.bank_report"),
        ("Bank Statement", "account_reports.bank_statement"),
        ("Cash Book", "account_reports.cash_book")
    ]
}

icons = {
    "Cash Out": "fa-money-bill-wave",
    "Expense": "fa-file-invoice",
    "Supplier": "fa-truck",
    "Purchase": "fa-cart-shopping",
    "Purchase Return": "fa-undo",
    "Customer": "fa-users",
    "Sale": "fa-bag-shopping",
    "Sale Return": "fa-rotate-left",
    "Customer Collection": "fa-money-bill-wave",
    "Account Reports": "fa-chart-line"
}

def to_snake(name):
    return name.replace(' ', '_').lower()

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
"""

for module, items in modules.items():
    bp_name = to_snake(module)
    icon = icons[module]
    collapse_id = f"collapse{bp_name}"
    heading_id = f"heading{bp_name}"
    
    # Use the first endpoint's prefix to check active state
    bp_match = items[0][1].split('.')[0] if items else ""
    
    sidebar_html += f"""
                <!-- {module} -->
                <div class="accordion-item bg-dark border-0">
                    <h2 class="accordion-header" id="{heading_id}">
                        <button class="accordion-button bg-dark text-white shadow-none collapsed d-flex align-items-center" type="button" data-bs-toggle="collapse" data-bs-target="#{collapse_id}" aria-expanded="{{% if '{bp_match}.' in request.endpoint %}}true{{% else %}}false{{% endif %}}" aria-controls="{collapse_id}" style="padding: 1rem 1.25rem;">
                            <i class="fa-solid {icon} me-3" style="width: 20px;"></i>
                            <span>{module}</span>
                        </button>
                    </h2>
                    <div id="{collapse_id}" class="accordion-collapse collapse {{% if '{bp_match}.' in request.endpoint %}}show{{% endif %}}" aria-labelledby="{heading_id}" data-bs-parent="#sidebarAccordion">
                        <div class="accordion-body p-0">
                            <div class="list-group list-group-flush bg-dark">
"""
    for title, endpoint in items:
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

print("Done")
