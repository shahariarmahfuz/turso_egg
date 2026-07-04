from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Admin, Business, generate_avatar_seed
import re

user_settings_bp = Blueprint('user_settings', __name__)

def is_valid_url(url):
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)

def _ensure_business_context():
    """Ensure g.business and g.business_slug are set for non-Site-Admin users.

    The user_settings routes are registered without the /business/<business_slug>
    prefix, so g.business_slug is None when these routes are hit.  base.html's
    sidebar generates URLs (url_for('routes.dashboard'), etc.) that require the
    business_slug parameter.  Without it Flask raises a BuildError → 500.
    """
    if current_user.role != 'Site Admin' and not getattr(g, 'business', None):
        if current_user.business_id:
            try:
                business = Business.query.get(current_user.business_id)
                if business:
                    g.business = business
                    g.business_slug = business.business_slug
            except Exception:
                pass

@user_settings_bp.route('/account/settings', methods=['GET'])
@login_required
def settings_page():
    try:
        # If site admin, render with site admin base layout, else normal base
        if current_user.role == 'Site Admin':
            base_template = 'site_admin_base.html'
        else:
            base_template = 'base.html'
            _ensure_business_context()
        return render_template('user_settings.html', base_template=base_template)
    except Exception:
        flash('An error occurred while loading settings. Please try again.', 'danger')
        if current_user.role == 'Site Admin':
            return redirect(url_for('site_admin.dashboard'))
        return redirect(url_for('auth.login'))

@user_settings_bp.route('/account/change_avatar', methods=['POST'])
@login_required
def change_avatar():
    try:
        action = request.form.get('action')
        
        if action == 'generate':
            current_user.avatar_seed = generate_avatar_seed()
            current_user.avatar_url = None
            db.session.commit()
            flash('Avatar updated successfully.', 'success')
            
        elif action == 'update_url':
            avatar_url = request.form.get('avatar_url', '').strip()
            
            if not avatar_url:
                current_user.avatar_url = None
                db.session.commit()
                flash('Avatar URL removed.', 'success')
            elif is_valid_url(avatar_url):
                current_user.avatar_url = avatar_url
                db.session.commit()
                flash('Avatar URL updated successfully.', 'success')
            else:
                flash('Invalid URL format.', 'danger')
    except Exception:
        db.session.rollback()
        flash('An error occurred while updating your avatar. Please try again.', 'danger')
            
    return redirect(request.referrer or url_for('user_settings.settings_page'))


@user_settings_bp.route('/account/change_password', methods=['POST'])
@login_required
def change_password():
    if current_user.role == 'Employee':
        flash('Employees cannot change their password.', 'danger')
        return redirect(request.referrer or url_for('user_settings.settings_page'))

    try:
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
    except Exception:
        db.session.rollback()
        flash('An error occurred while changing your password. Please try again.', 'danger')

    return redirect(request.referrer or url_for('user_settings.settings_page'))
