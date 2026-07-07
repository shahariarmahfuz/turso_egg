from app import create_app
from models import db, Admin
from werkzeug.security import generate_password_hash
app = create_app()
with app.app_context():
    admin = Admin.query.filter_by(username='siteadmin').first()
    admin.password = generate_password_hash('password')
    db.session.commit()
