from app import create_app
from models import Admin
app = create_app()
with app.app_context():
    print(Admin.query.filter_by(username='siteadmin').first().role)
