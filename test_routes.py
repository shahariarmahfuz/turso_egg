from app import create_app
from models import db, Admin

app = create_app()
app.config['TESTING'] = True

with app.test_client() as client:
    with app.app_context():
        admin = Admin.query.filter_by(username='admin').first()
        
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)
        sess['_fresh'] = True

    # Test all key routes
    routes = [
        '/dashboard',
        '/cash_out/add', '/cash_out/manage',
        '/sale/add_sale', '/sale/manage_sale', '/sale/sale_report', '/sale/sale_item_report',
        '/customer/add_customer', '/customer/manage_customer',
        '/supplier/add_supplier', '/supplier/manage_supplier',
        '/purchase/add_purchase', '/purchase/manage_purchase',
        '/purchase_return/add_purchase_return', '/purchase_return/manage_purchase_return',
        '/sale_return/add_sale_return', '/sale_return/manage_sale_return', '/sale_return/sale_return_report',
        '/customer_collection/collection', '/customer_collection/manage_collection', '/customer_collection/collections_report',
        '/account_reports/expense_report', '/account_reports/income_report',
        '/account_reports/bank_report', '/account_reports/bank_statement', '/account_reports/cash_book',
    ]
    
    errors = []
    for r in routes:
        resp = client.get(r)
        status = "OK" if resp.status_code == 200 else f"FAIL ({resp.status_code})"
        if resp.status_code != 200:
            errors.append(f"{r} -> {resp.status_code}")
        print(f"  {status}  {r}")
    
    print(f"\n{'='*50}")
    if errors:
        print(f"FAILURES ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print(f"ALL {len(routes)} ROUTES PASSED ✓")
