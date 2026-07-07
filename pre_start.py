import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    if os.environ.get('AUTO_MIGRATE_ON_START', 'true').lower() != 'true':
        logging.info("AUTO_MIGRATE_ON_START is disabled. Skipping database migration check.")
        sys.exit(0)

    try:
        from app import create_app
        from models import db
        import flask_migrate
        from alembic.migration import MigrationContext
        from alembic.script import ScriptDirectory

        app = create_app()

        with app.app_context():
            # 1. Verify Database Connectivity
            try:
                with db.engine.connect() as conn:
                    logging.info("Database connection verified.")
                    
                    # 2. Check Alembic Initialization
                    if not os.path.exists('migrations'):
                        logging.error("Migrations directory not found. Cannot perform startup check.")
                        sys.exit(1)
                        
                    # 3. Read current migration version
                    context = MigrationContext.configure(conn)
                    current_rev = context.get_current_revision()

            except Exception as e:
                logging.error(f"Database connectivity failed: {e}")
                sys.exit(1)

            # 4. Compare with head
            try:
                script = ScriptDirectory("migrations")
                head_rev = script.get_current_head()
            except Exception as e:
                logging.error(f"Failed to read Alembic head revision: {e}")
                sys.exit(1)

            if current_rev != head_rev:
                logging.info(f"Pending migrations detected. Current: {current_rev}, Head: {head_rev}")
                logging.info("Executing alembic upgrade head...")
                try:
                    flask_migrate.upgrade()
                    logging.info("Migration successful.")
                except Exception as e:
                    logging.error(f"Migration failed: {e}")
                    sys.exit(1)
            else:
                logging.info(f"Database is up to date (Revision: {current_rev}).")
                
            # Ensure Site Admin exists
            from werkzeug.security import generate_password_hash
            from models import Admin
            try:
                if not Admin.query.filter_by(username='siteadmin', role='Site Admin').first():
                    site_admin = Admin(username='siteadmin', password=generate_password_hash('admin'), role='Site Admin')
                    db.session.add(site_admin)
                    db.session.commit()
                    logging.info("Initial Site Admin account created.")
            except Exception as e:
                logging.error(f"Site Admin creation error: {e}")
                sys.exit(1)

    except Exception as e:
        logging.error(f"Pre-start script encountered an unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
