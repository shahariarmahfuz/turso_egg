from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from auth import admin_required
from models import db, ExpenseHead, ExpenseEntry
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expense')

@login_required
@expenses_bp.route('/add_expense_head', methods=['GET', 'POST'])
def add_expense_head():
    if request.method == 'POST':
        head_name = request.form.get('head_name')
        date_str = request.form.get('date')
        
        if ExpenseHead.query.filter_by(head_name=head_name).first():
            flash('Expense Head already exists.', 'danger')
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
            new_head = ExpenseHead(head_name=head_name, created_date=date_obj)
            db.session.add(new_head)
            db.session.commit()
            flash('Expense Head added successfully.', 'success')
            return redirect(url_for('expenses.manage_expense_head'))
    return render_template('expense_head_form.html', action="Add")

@login_required
@expenses_bp.route('/manage_expense_head')
def manage_expense_head():
    heads = ExpenseHead.query.order_by(ExpenseHead.id.desc()).all()
    return render_template('manage_expense_head.html', heads=heads)

@login_required
@expenses_bp.route('/edit_expense_head/<int:id>', methods=['GET', 'POST'])
def edit_expense_head(id):
    head = ExpenseHead.query.get_or_404(id)
    if request.method == 'POST':
        head_name = request.form.get('head_name')
        existing = ExpenseHead.query.filter_by(head_name=head_name).first()
        if existing and existing.id != id:
            flash('Another Expense Head with this name already exists.', 'danger')
        else:
            head.head_name = head_name
            db.session.commit()
            flash('Expense Head updated successfully.', 'success')
            return redirect(url_for('expenses.manage_expense_head'))
    return render_template('expense_head_form.html', action="Edit", head=head)

@login_required
@expenses_bp.route('/delete_expense_head/<int:id>', methods=['POST'])
def delete_expense_head(id):
    head = ExpenseHead.query.get_or_404(id)
    db.session.delete(head)
    db.session.commit()
    flash('Expense Head deleted successfully.', 'success')
    return redirect(url_for('expenses.manage_expense_head'))

@login_required
@expenses_bp.route('/add_expense_entry', methods=['GET', 'POST'])
def add_expense_entry():
    heads = ExpenseHead.query.all()
    if request.method == 'POST':
        date_str = request.form.get('date')
        expense_head_id = request.form.get('expense_head_id')
        amount = request.form.get('amount')
        comment = request.form.get('comment')
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            amount_val = float(amount)
            if not expense_head_id:
                flash("Expense Head is required.", "danger")
            elif amount_val <= 0:
                flash("Amount must be greater than 0.", "danger")
            else:
                entry = ExpenseEntry(
                    date=date_obj,
                    expense_head_id=expense_head_id,
                    amount=amount_val,
                    comment=comment
                )
                db.session.add(entry)
                db.session.commit()
                flash('Daily Expense added successfully.', 'success')
                return redirect(url_for('expenses.manage_daily_expense'))
        except Exception as e:
            flash(f"Error saving entry: {e}", "danger")
            
    return render_template('expense_entry_form.html', action="Add", heads=heads)

@login_required
@expenses_bp.route('/manage_daily_expense')
def manage_daily_expense():
    heads = ExpenseHead.query.all()
    query = ExpenseEntry.query

    search_date = request.args.get('date')
    expense_head_id = request.args.get('expense_head_id')

    if search_date:
        query = query.filter(ExpenseEntry.date == datetime.strptime(search_date, '%Y-%m-%d').date())
    if expense_head_id:
        query = query.filter(ExpenseEntry.expense_head_id == expense_head_id)

    entries = query.order_by(ExpenseEntry.date.desc(), ExpenseEntry.id.desc()).all()
    total_amount = sum(entry.amount for entry in entries)

    return render_template('manage_daily_expense.html', entries=entries, heads=heads, total_amount=total_amount)

@login_required
@expenses_bp.route('/edit_expense_entry/<int:id>', methods=['GET', 'POST'])
def edit_expense_entry(id):
    entry = ExpenseEntry.query.get_or_404(id)
    heads = ExpenseHead.query.all()
    if request.method == 'POST':
        date_str = request.form.get('date')
        expense_head_id = request.form.get('expense_head_id')
        amount = request.form.get('amount')
        comment = request.form.get('comment')
        
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                flash("Amount must be greater than 0.", "danger")
            else:
                entry.date = datetime.strptime(date_str, '%Y-%m-%d').date()
                entry.expense_head_id = expense_head_id
                entry.amount = amount_val
                entry.comment = comment
                db.session.commit()
                flash('Daily Expense updated successfully.', 'success')
                return redirect(url_for('expenses.manage_daily_expense'))
        except Exception as e:
            flash(f"Error updating entry: {e}", "danger")
            
    return render_template('expense_entry_form.html', action="Edit", entry=entry, heads=heads)

@login_required
@expenses_bp.route('/delete_expense_entry/<int:id>', methods=['POST'])
def delete_expense_entry(id):
    entry = ExpenseEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Daily Expense deleted successfully.', 'success')
    return redirect(url_for('expenses.manage_daily_expense'))
