import os

files_to_convert = {
    'collection_form.html': 'payment_form.html',
    'manage_collection.html': 'manage_payment.html',
    'collections_report.html': 'payments_report.html'
}

for src, dst in files_to_convert.items():
    with open(f'templates/{src}', 'r') as f:
        content = f.read()

    # Replacements
    content = content.replace('customer_collection_bp', 'supplier_payment_bp')
    content = content.replace('customer_collection', 'supplier_payment')
    content = content.replace('CustomerCollection', 'SupplierPayment')
    content = content.replace('CustomerLedger', 'SupplierLedger')
    content = content.replace('Customer Collection', 'Supplier Payment')
    content = content.replace('customer collection', 'supplier payment')
    content = content.replace('Customer', 'Supplier')
    content = content.replace('customer', 'supplier')
    content = content.replace('Collection', 'Payment')
    content = content.replace('collection', 'payment')
    content = content.replace('COL-', 'SP-')

    with open(f'templates/{dst}', 'w') as f:
        f.write(content)
