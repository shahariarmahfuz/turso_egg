from flask import Flask, g, request, redirect, url_for
from models import db, Admin, Business
from flask_login import LoginManager
from auth import auth_bp
from routes import routes_bp
from site_admin import site_admin_bp

import os
from dotenv import load_dotenv
from flask_migrate import Migrate

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    auth_token = os.environ.get('TURSO_AUTH_TOKEN')
    if auth_token:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {'auth_token': auth_token}
        }


    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/site-admin'):
            return redirect(url_for('site_admin.login'))
        elif getattr(g, 'business_slug', None):
            return redirect(url_for('auth.login', next=request.path))
        else:
            return redirect(url_for('auth.login'))

    @app.url_value_preprocessor
    def pull_business_slug(endpoint, values):
        if values and 'business_slug' in values:
            g.business_slug = values.pop('business_slug')
            g.business = Business.query.filter_by(business_slug=g.business_slug).first()
        else:
            g.business_slug = None
            g.business = None

    from flask_login import current_user
    from flask import flash
    @app.before_request
    def check_business_access():
        if getattr(g, 'business', None) and current_user.is_authenticated:
            if current_user.role == 'Site Admin' or current_user.business_id != g.business.id:
                # If site admin or wrong business, deny access
                flash('Access Denied. You do not have permission for this business.', 'danger')
                if current_user.role == 'Site Admin':
                    return redirect(url_for('site_admin.dashboard'))
                else:
                    return redirect(url_for('auth.login'))

    @app.url_defaults
    def add_business_slug(endpoint, values):
        if 'business_slug' in values or not getattr(g, 'business_slug', None):
            return
        if endpoint in app.view_functions:
            try:
                for rule in app.url_map.iter_rules(endpoint):
                    if 'business_slug' in rule.arguments:
                        values['business_slug'] = g.business_slug
                        break
            except KeyError:
                pass

    app.register_blueprint(site_admin_bp)
    
    # We prefix auth routes with /dashboard
    app.register_blueprint(auth_bp, url_prefix='/dashboard')
    
    business_prefix = '/business/<business_slug>'
    app.register_blueprint(routes_bp, url_prefix=business_prefix)

    from expenses import expenses_bp
    from supplier import supplier_bp
    from cash_out import cash_out_bp
    from purchase import purchase_bp
    from purchase_return import purchase_return_bp
    from customer import customer_bp
    from sale import sale_bp
    from sale_return import sale_return_bp
    from customer_collection import customer_collection_bp
    from supplier_payment import supplier_payment_bp
    from account_reports import account_reports_bp
    from users import users_bp
    from product import product_bp
    from user_settings import user_settings_bp

    app.register_blueprint(user_settings_bp)
    app.register_blueprint(expenses_bp, url_prefix=business_prefix + '/expenses')
    app.register_blueprint(cash_out_bp, url_prefix=business_prefix + '/cash_out')
    app.register_blueprint(supplier_bp, url_prefix=business_prefix + '/supplier')
    app.register_blueprint(purchase_bp, url_prefix=business_prefix + '/purchase')
    app.register_blueprint(purchase_return_bp, url_prefix=business_prefix + '/purchase_return')
    app.register_blueprint(customer_bp, url_prefix=business_prefix + '/customer')
    app.register_blueprint(sale_bp, url_prefix=business_prefix + '/sale')
    app.register_blueprint(sale_return_bp, url_prefix=business_prefix + '/sale_return')
    app.register_blueprint(customer_collection_bp, url_prefix=business_prefix + '/customer_collection')
    app.register_blueprint(supplier_payment_bp, url_prefix=business_prefix + '/supplier_payment')
    app.register_blueprint(account_reports_bp, url_prefix=business_prefix + '/account_reports')
    app.register_blueprint(users_bp, url_prefix=business_prefix + '/users')
    app.register_blueprint(product_bp, url_prefix=business_prefix + '/product')

    @app.route('/status')
    def status():
        return 'Status: OK', 200

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    with app.app_context():
        # Ensure database is connected and initialized safely
        try:
            db.engine.connect()
            print("Database connection verified.")

            # Attempt automatic migrations safely
            try:
                import flask_migrate
                
                if not os.path.exists('migrations'):
                    try:
                        flask_migrate.init()
                    except BaseException as e:
                        print(f"Init warning: {e}")
                
                # 1. Ensure all tables exist from models first.
                #    This prevents migrations from trying to ALTER
                #    tables that don't exist yet on a fresh database.
                db.create_all()
                
                # 2. Apply existing migrations (all are idempotent,
                #    so they safely skip work already done by create_all).
                try:
                    flask_migrate.upgrade()
                except BaseException as e:
                    print(f"Upgrade warning: {e}")
                
                # 3. Stamp to ensure alembic_version is at the
                #    current head revision.
                try:
                    flask_migrate.stamp()
                except BaseException as e:
                    print(f"Stamp warning: {e}")
                    
            except BaseException as e:
                print(f"Migration phase skipped/error: {e}")

            # Ensure Site Admin exists
            from werkzeug.security import generate_password_hash
            from models import Admin
            try:
                if not Admin.query.filter_by(username='siteadmin', role='Site Admin').first():
                    site_admin = Admin(username='siteadmin', password=generate_password_hash('admin'), role='Site Admin')
                    db.session.add(site_admin)
                    db.session.commit()
                    print("Initial Site Admin account created.")
            except Exception as e:
                print(f"Site Admin creation error: {e}")
                
        except Exception as e:
            print(f"Startup check failed: {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
