from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import Admin
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            if admin.status != 'Active':
                flash('Your account is inactive. Please contact admin.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(admin)
            session['role'] = admin.role
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
