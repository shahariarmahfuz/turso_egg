from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE businesses ADD COLUMN dashboard_baseline_date DATE;"))
        db.session.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error adding column: {e}")
