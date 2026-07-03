from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Admin, generate_avatar_seed

user_settings_bp = Blueprint('user_settings', __name__)

@user_settings_bp.route('/account/settings', methods=['GET'])
@login_required
def settings_page():
    # If site admin, render with site admin base layout, else normal base
    if current_user.role == 'Site Admin':
        base_template = 'site_admin_base.html'
    else:
        base_template = 'base.html'
    return render_template('user_settings.html', base_template=base_template)

@user_settings_bp.route('/account/change_avatar', methods=['POST'])
@login_required
def change_avatar():
    current_user.avatar_seed = generate_avatar_seed()
    db.session.commit()
    flash('Avatar updated successfully.', 'success')
    return redirect(request.referrer or url_for('user_settings.settings_page'))

@user_settings_bp.route('/account/change_password', methods=['POST'])
@login_required
def change_password():
    if current_user.role == 'Employee':
        flash('Employees cannot change their password.', 'danger')
        return redirect(request.referrer or url_for('user_settings.settings_page'))
        
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(request.referrer or url_for('user_settings.settings_page'))
        
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(request.referrer or url_for('user_settings.settings_page'))
        
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(request.referrer or url_for('user_settings.settings_page'))
