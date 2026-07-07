from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Admin, dhaka_now
from auth import admin_required
from datetime import datetime

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@users_bp.route('/settings')
@login_required
@admin_required
def settings():
    return render_template('settings.html')

@users_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        role = request.form.get('role')
        password = request.form.get('password')
        
        # Check if username exists
        if Admin.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('users.add_user'))
            
        hashed_pw = generate_password_hash(password)
        new_user = Admin(
            name=name,
            username=username,
            role=role,
            password=hashed_pw,
            status='Active',
            created_at=dhaka_now(),
            updated_at=dhaka_now()
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully.', 'success')
        return redirect(url_for('users.manage_users'))
        
    return render_template('add_user.html')

@users_bp.route('/manage')
@login_required
@admin_required
def manage_users():
    users = Admin.query.filter(Admin.is_hidden == False).all()
    return render_template('manage_users.html', users=users)

@users_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    from flask import abort
    user = Admin.query.get_or_404(id)
    if getattr(user, 'is_hidden', False):
        abort(403)
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.role = request.form.get('role')
        user.status = request.form.get('status')
        
        password = request.form.get('password')
        if password:
            user.password = generate_password_hash(password)
            
        user.updated_at = dhaka_now()
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('users.manage_users'))
        
    return render_template('edit_user.html', user=user)

@users_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    if id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('users.manage_users'))
        
    user = Admin.query.get_or_404(id)
    from flask import abort
    if getattr(user, 'is_hidden', False):
        abort(403)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('users.manage_users'))
