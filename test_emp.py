from app import create_app
from models import db, Admin
from werkzeug.security import generate_password_hash

app = create_app()
app.config['TESTING'] = True

with app.test_client() as client:
    with app.app_context():
        # Create employee user
        emp = Admin.query.filter_by(username='emp').first()
        if not emp:
            emp = Admin(username='emp', password=generate_password_hash('emp'), role='Employee')
            db.session.add(emp)
            db.session.commit()
        
        emp_id = str(emp.id)
        
    with client.session_transaction() as sess:
        sess['_user_id'] = emp_id
        sess['_fresh'] = True

    resp = client.get('/users/manage')
    print(f"Employee accessing /users/manage (Admin only): {resp.status_code} (Expected 403)")

    resp = client.get('/account_reports/bank_statement')
    print(f"Employee accessing /account_reports/bank_statement (Admin only): {resp.status_code} (Expected 403)")

    resp = client.get('/dashboard')
    print(f"Employee accessing /dashboard (Allowed): {resp.status_code} (Expected 200)")
