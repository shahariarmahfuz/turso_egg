from app import create_app
from models import db, Admin, generate_avatar_seed

app = create_app()

with app.app_context():
    admins = Admin.query.filter(Admin.avatar_seed == None).all()
    for admin in admins:
        admin.avatar_seed = generate_avatar_seed()
    db.session.commit()
    print(f"Updated {len(admins)} existing admins with avatar seeds.")
