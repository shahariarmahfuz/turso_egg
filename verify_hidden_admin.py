import os
from app import create_app
from models import db, Admin, Business
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    business = Business.query.first()
    if not business:
        business = Business(business_name='Test', business_slug='test')
        db.session.add(business)
        db.session.commit()
    
    # 1. Create a SiteAdmin (if not exists)
    site_admin = Admin.query.filter_by(username='siteadmin').first()
    if not site_admin:
        site_admin = Admin(
            username='siteadmin',
            password=generate_password_hash('password'),
            role='Site Admin',
            status='Active'
        )
        db.session.add(site_admin)
        
    # 2. Create a Business Admin
    bus_admin = Admin.query.filter_by(username='busadmin').first()
    if not bus_admin:
        bus_admin = Admin(
            username='busadmin',
            password=generate_password_hash('password'),
            role='Admin',
            status='Active',
            business_id=business.id
        )
        db.session.add(bus_admin)
        
    # 3. Create a Hidden Admin
    hidden_admin = Admin.query.filter_by(username='hiddenadmin').first()
    if not hidden_admin:
        hidden_admin = Admin(
            username='hiddenadmin',
            password=generate_password_hash('password'),
            role='Admin',
            status='Active',
            is_hidden=True,
            business_id=business.id
        )
        db.session.add(hidden_admin)
        
    db.session.commit()
    
    print("Test users created successfully.")
