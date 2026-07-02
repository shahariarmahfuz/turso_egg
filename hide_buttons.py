import os
import re

files_to_process = [
    'templates/manage_purchase_return.html',
    'templates/manage_expense_head.html',
    'templates/manage_sale_return.html',
    'templates/manage_cash_out.html',
    'templates/manage_supplier.html',
    'templates/manage_sale.html',
    'templates/manage_collection.html',
    'templates/manage_purchase.html',
    'templates/manage_daily_expense.html',
    'templates/manage_customer.html'
]

for filename in files_to_process:
    filepath = os.path.join('/workspaces/egg', filename)
    with open(filepath, 'r') as f:
        content = f.read()

    # We want to wrap `<a ... edit...` and `<form ... delete...` in `{% if current_user.role == 'Admin' %}` ... `{% endif %}`
    
    # We'll split the file by lines and look for "btn-primary" (edit) and "btn-danger" (delete form) or `<form action="...delete...`
    lines = content.split('\n')
    new_lines = []
    
    in_admin_block = False
    for i, line in enumerate(lines):
        if 'edit_' in line and 'btn-primary' in line and '{% if current_user.role' not in line:
            new_lines.append(line.replace('<a href=', "{% if current_user.role == 'Admin' %}\n                            <a href="))
        elif '<form action=' in line and 'delete_' in line and '{% if current_user.role' not in line:
            if '{% if current_user.role' not in new_lines[-1]:
                new_lines.append("{% if current_user.role == 'Admin' %}")
            new_lines.append(line)
            in_admin_block = True
        elif '</form>' in line and in_admin_block:
            new_lines.append(line)
            new_lines.append("                            {% endif %}")
            in_admin_block = False
        # Manage Expense Head uses edit directly without `edit_` prefix sometimes?
        elif 'edit' in line and 'btn-primary' in line and '{% if current_user.role' not in line:
            new_lines.append(line.replace('<a href=', "{% if current_user.role == 'Admin' %}\n                            <a href="))
        elif '<form action=' in line and 'delete' in line and '{% if current_user.role' not in line and not in_admin_block:
            if '{% if current_user.role' not in new_lines[-1]:
                new_lines.append("                            {% if current_user.role == 'Admin' %}")
            new_lines.append(line)
            in_admin_block = True
        else:
            new_lines.append(line)

    with open(filepath, 'w') as f:
        f.write('\n'.join(new_lines))

print("Done hiding buttons")
