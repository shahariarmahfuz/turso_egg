import os

with open('/workspaces/egg/purchase.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I need to add SupplierLedger logic inside purchase.py
old_logic = """            # Update Supplier Due
            sup = Supplier.query.get(supplier_id)
            if sup and due_amount > 0:
                sup.current_balance += due_amount"""

new_logic = """            # Update Supplier Due and Ledger
            sup = Supplier.query.get(supplier_id)
            if sup:
                sup.current_balance += due_amount
                
                if due_amount > 0 or total_amount > 0:
                    from models import SupplierLedger
                    ledger_desc = f"Purchase Invoice: {new_purchase.invoice_no}"
                    ledger = SupplierLedger(
                        supplier_id=sup.id,
                        date=purchase_date,
                        invoice_no=new_purchase.invoice_no,
                        description=ledger_desc,
                        credit=total_amount,
                        debit=cash_paid,
                        balance=sup.current_balance
                    )
                    db.session.add(ledger)"""

content = content.replace(old_logic, new_logic)

with open('/workspaces/egg/purchase.py', 'w', encoding='utf-8') as f:
    f.write(content)
