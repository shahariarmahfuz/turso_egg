from flask import Flask
from models import db, Admin
from flask_login import LoginManager
from auth import auth_bp
from routes import routes_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)


    from expenses import expenses_bp
    app.register_blueprint(expenses_bp)

    from supplier import supplier_bp
    from cash_out import cash_out_bp
    from purchase import purchase_bp
    from purchase_return import purchase_return_bp
    from customer import customer_bp
    from sale import sale_bp
    from sale_return import sale_return_bp
    from customer_collection import customer_collection_bp
    from account_reports import account_reports_bp
    from users import users_bp

    app.register_blueprint(cash_out_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(purchase_bp)
    app.register_blueprint(purchase_return_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(sale_bp)
    app.register_blueprint(sale_return_bp)
    app.register_blueprint(customer_collection_bp)
    app.register_blueprint(account_reports_bp)
    app.register_blueprint(users_bp, url_prefix='/users')

    with app.app_context():
        db.create_all()
        # Create a default admin if not exists
        from werkzeug.security import generate_password_hash
        if not Admin.query.filter_by(username='admin').first():
            default_admin = Admin(username='admin', password=generate_password_hash('admin'))
            db.session.add(default_admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
