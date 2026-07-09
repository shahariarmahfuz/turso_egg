from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

def run_migration():
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE customer_collections ADD COLUMN updated_by INTEGER;"))
            print("Added updated_by")
        except Exception as e:
            print(f"Skipped updated_by: {e}")
            db.session.rollback()

        try:
            db.session.execute(text("ALTER TABLE customer_collections ADD COLUMN updated_at DATETIME;"))
            print("Added updated_at")
        except Exception as e:
            print(f"Skipped updated_at: {e}")
            db.session.rollback()
        
        db.session.commit()

if __name__ == '__main__':
    run_migration()
