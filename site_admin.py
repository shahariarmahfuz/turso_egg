from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Admin, Business
from functools import wraps

site_admin_bp = Blueprint('site_admin', __name__, url_prefix='/site-admin')

def site_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Site Admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('site_admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@site_admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.role == 'Site Admin':
        return redirect(url_for('site_admin.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            if admin.role != 'Site Admin':
                flash('Access Denied. This portal is reserved for Site Administrators.', 'danger')
                return redirect(url_for('site_admin.login'))
            login_user(admin)
            return redirect(url_for('site_admin.dashboard'))
        flash('Invalid Site Admin credentials.', 'danger')
    return render_template('site_admin_login.html')

@site_admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('site_admin.login'))

@site_admin_bp.route('/dashboard')
@login_required
@site_admin_required
def dashboard():
    businesses = Business.query.all()
    return render_template('site_admin_dashboard.html', businesses=businesses)

@site_admin_bp.route('/business/create', methods=['POST'])
@login_required
@site_admin_required
def create_business():
    name = request.form.get('business_name')
    slug = request.form.get('business_slug')
    baseline_str = request.form.get('dashboard_baseline_date')
    baseline_date = None
    if baseline_str:
        from datetime import datetime
        from models import dhaka_now_date
        try:
            parsed_date = datetime.strptime(baseline_str, '%Y-%m-%d').date()
            if parsed_date > dhaka_now_date():
                flash('Dashboard baseline date cannot be in the future.', 'danger')
                return redirect(url_for('site_admin.dashboard'))
            baseline_date = parsed_date
        except ValueError:
            pass

    new_business = Business(business_name=name, business_slug=slug, dashboard_baseline_date=baseline_date)
    db.session.add(new_business)
    try:
        db.session.commit()
        flash('Business created.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating business (slug must be unique).', 'danger')
    return redirect(url_for('site_admin.dashboard'))

@site_admin_bp.route('/business/edit/<int:id>', methods=['POST'])
@login_required
@site_admin_required
def edit_business(id):
    business = Business.query.get_or_404(id)
    business.business_name = request.form.get('business_name')
    business.business_slug = request.form.get('business_slug')
    
    baseline_str = request.form.get('dashboard_baseline_date')
    if baseline_str:
        from datetime import datetime
        from models import dhaka_now_date
        try:
            parsed_date = datetime.strptime(baseline_str, '%Y-%m-%d').date()
            if parsed_date > dhaka_now_date():
                flash('Dashboard baseline date cannot be in the future.', 'danger')
                return redirect(url_for('site_admin.dashboard'))
            business.dashboard_baseline_date = parsed_date
        except ValueError:
            pass
    else:
        business.dashboard_baseline_date = None

    db.session.commit()
    flash('Business updated.', 'success')
    return redirect(url_for('site_admin.dashboard'))

@site_admin_bp.route('/business/status/<int:id>/<status>')
@login_required
@site_admin_required
def business_status(id, status):
    business = Business.query.get_or_404(id)
    business.status = 'Active' if status == 'activate' else 'Inactive'
    db.session.commit()
    flash('Business status updated.', 'success')
    return redirect(url_for('site_admin.dashboard'))

@site_admin_bp.route('/business/delete/<int:id>')
@login_required
@site_admin_required
def delete_business(id):
    business = Business.query.get_or_404(id)
    try:
        # Safely delete all related records that have business_id
        for table in reversed(db.metadata.sorted_tables):
            if 'business_id' in table.columns:
                db.session.execute(table.delete().where(table.c.business_id == id))
                
        # Now delete the business
        db.session.delete(business)
        db.session.commit()
        flash('Business deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting business: {str(e)}', 'danger')
        
    return redirect(url_for('site_admin.dashboard'))

@site_admin_bp.route('/users/<int:business_id>')
@login_required
@site_admin_required
def manage_users(business_id):
    business = Business.query.get_or_404(business_id)
    users = Admin.query.filter_by(business_id=business_id).all()
    return render_template('site_admin_users.html', business=business, users=users)

@site_admin_bp.route('/users/<int:business_id>/add', methods=['POST'])
@login_required
@site_admin_required
def add_user(business_id):
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    name = request.form.get('name')
    is_hidden = request.form.get('is_hidden') == 'on'
    user = Admin(
        username=username, 
        password=generate_password_hash(password), 
        role=role, 
        name=name, 
        business_id=business_id,
        is_hidden=is_hidden
    )
    db.session.add(user)
    try:
        db.session.commit()
        flash('User added.', 'success')
    except:
        db.session.rollback()
        flash('Error adding user. Username may exist.', 'danger')
    return redirect(url_for('site_admin.manage_users', business_id=business_id))

@site_admin_bp.route('/users/<int:business_id>/edit/<int:user_id>', methods=['POST'])
@login_required
@site_admin_required
def edit_user(business_id, user_id):
    user = Admin.query.get_or_404(user_id)
    user.name = request.form.get('name')
    user.role = request.form.get('role')
    user.is_hidden = request.form.get('is_hidden') == 'on'
    password = request.form.get('password')
    if password:
        user.password = generate_password_hash(password)
        
    avatar_url = request.form.get('avatar_url')
    if avatar_url is not None:
        avatar_url = avatar_url.strip()
        if not avatar_url:
            user.avatar_url = None
        else:
            import re
            regex = re.compile(
                r'^https?://'
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
                r'localhost|'
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                r'(?::\d+)?'
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if regex.search(avatar_url):
                user.avatar_url = avatar_url
            else:
                flash('Invalid Avatar URL format ignored.', 'warning')

    db.session.commit()
    flash('User updated.', 'success')
    return redirect(url_for('site_admin.manage_users', business_id=business_id))

@site_admin_bp.route('/users/<int:business_id>/delete/<int:user_id>')
@login_required
@site_admin_required
def delete_user(business_id, user_id):
    user = Admin.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('site_admin.manage_users', business_id=business_id))

