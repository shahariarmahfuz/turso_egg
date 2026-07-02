import os
import re

files_to_update = {
    'cash_out.py': ['edit', 'delete'],
    'customer.py': ['edit_customer', 'delete_customer'],
    'customer_collection.py': ['delete_collection'],
    'expenses.py': ['edit_expense_head', 'delete_expense_head', 'edit_expense_entry', 'delete_expense_entry'],
    'purchase.py': ['delete_purchase'],
    'purchase_return.py': ['delete_purchase_return'],
    'sale.py': ['delete_sale'],
    'sale_return.py': ['delete_sale_return'],
    'supplier.py': ['edit_supplier', 'delete_supplier']
}

for filename, funcs in files_to_update.items():
    filepath = os.path.join('/workspaces/egg', filename)
    with open(filepath, 'r') as f:
        content = f.read()

    # ensure the import exists (also customer_collection.py didn't match the sed because it had , current_user)
    if 'from auth import admin_required' not in content:
        content = content.replace('from flask_login import login_required', 'from flask_login import login_required\nfrom auth import admin_required')
        content = content.replace('from flask_login import login_required, current_user', 'from flask_login import login_required, current_user\nfrom auth import admin_required')

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        if line.startswith('@') and '.route(' in line:
            # check if the next line is @login_required
            if i + 1 < len(lines) and lines[i+1].strip() == '@login_required':
                # check if the function defined next is one we want to protect
                # find the def line
                def_idx = i + 2
                while def_idx < len(lines) and not lines[def_idx].startswith('def '):
                    def_idx += 1
                if def_idx < len(lines):
                    func_name = lines[def_idx].split(' ')[1].split('(')[0]
                    if func_name in funcs:
                        # add @admin_required after @login_required
                        new_lines.append(lines[i+1])
                        new_lines.append('@admin_required')
                        i += 1
        i += 1
    
    with open(filepath, 'w') as f:
        f.write('\n'.join(new_lines))

print("Done decorating routes")
