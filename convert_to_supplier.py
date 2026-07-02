with open('supplier_payment.py', 'r') as f:
    content = f.read()

content = content.replace('customer_collection_bp', 'supplier_payment_bp')
content = content.replace('customer_collection', 'supplier_payment')
content = content.replace('CustomerCollection', 'SupplierPayment')
content = content.replace('CustomerLedger', 'SupplierLedger')
content = content.replace('Customer', 'Supplier')
content = content.replace('customer', 'supplier')
content = content.replace('collection', 'payment')
content = content.replace('Collection', 'Payment')
content = content.replace('COL-', 'SP-')

with open('supplier_payment.py', 'w') as f:
    f.write(content)
