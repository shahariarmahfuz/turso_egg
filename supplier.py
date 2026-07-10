from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import or_
from flask_login import login_required
from auth import admin_required
from models import db, Supplier, dhaka_now
from datetime import datetime

supplier_bp = Blueprint('supplier', __name__, url_prefix='/supplier')

@login_required
@supplier_bp.route('/search_supplier', methods=['GET'])
def search_supplier():
    q = request.args.get('q', '').strip()
    if not q:
        suppliers = Supplier.query.limit(20).all()
    else:
        suppliers = Supplier.query.filter(
            or_(
                Supplier.supplier_name.ilike(f'%{q}%'),
                Supplier.supplier_code.ilike(f'%{q}%'),
                Supplier.contact_number.ilike(f'%{q}%')
            )
        ).limit(20).all()
    
    results = []
    for s in suppliers:
        results.append({
            'id': s.id,
            'text': f"{s.supplier_name} ({s.contact_number or 'N/A'}) - {s.supplier_code}"
        })
    return jsonify(results)

@login_required
@supplier_bp.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        supplier_name = request.form.get('supplier_name')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')
        previous_balance = request.form.get('previous_balance', 0.0)
        date_str = request.form.get('date')

        try:
            prev_bal_val = float(previous_balance)
            if Supplier.query.filter_by(supplier_name=supplier_name).first():
                flash("Supplier name already exists.", "danger")
            else:
                if contact_number and len(contact_number.strip()) < 7:
                    flash("Please enter a valid contact number.", "danger")
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else dhaka_now().date()
                    new_sup = Supplier(
                        supplier_name=supplier_name,
                        address=address,
                        contact_number=contact_number,
                        previous_balance=prev_bal_val,
                        current_balance=prev_bal_val,
                        created_date=date_obj
                    )
                    db.session.add(new_sup)
                    db.session.commit()
                    flash("Supplier added successfully.", "success")
                    return redirect(url_for('supplier.add_supplier'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            
    return render_template('supplier_form.html', action="Add")

@login_required
@supplier_bp.route('/manage_supplier')
def manage_supplier():
    suppliers = Supplier.query.order_by(Supplier.id.desc()).all()
    return render_template('manage_supplier.html', suppliers=suppliers)

@login_required
@admin_required
@supplier_bp.route('/edit_supplier/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    sup = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        supplier_name = request.form.get('supplier_name')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')
        previous_balance = request.form.get('previous_balance', 0.0)

        existing = Supplier.query.filter_by(supplier_name=supplier_name).first()
        if existing and existing.id != id:
            flash("Supplier name already exists.", "danger")
        else:
            try:
                prev_bal_val = float(previous_balance)
                diff = prev_bal_val - sup.previous_balance
                sup.current_balance += diff
                sup.previous_balance = prev_bal_val
                sup.supplier_name = supplier_name
                sup.address = address
                sup.contact_number = contact_number
                db.session.commit()
                flash("Supplier updated successfully.", "success")
                return redirect(url_for('supplier.manage_supplier'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {e}", "danger")
    return render_template('supplier_form.html', action="Edit", supplier=sup)

@login_required
@supplier_bp.route('/delete_supplier/<int:id>', methods=['POST'])
def delete_supplier(id):
    sup = Supplier.query.get_or_404(id)
    # Placeholder: Prevent deletion if Purchase or Payment records exist
    # if sup.purchases:
    #     flash("Cannot delete supplier with existing purchase records.", "danger")
    #     return redirect(url_for('supplier.manage_supplier'))
    db.session.delete(sup)
    db.session.commit()
    flash("Supplier deleted successfully.", "success")
    return redirect(url_for('supplier.manage_supplier'))

@login_required
@supplier_bp.route('/supplier_ledger', methods=['GET'])
def supplier_ledger():
    suppliers = Supplier.query.all()
    supplier_id = request.args.get('supplier_id')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    ledger_data = []
    opening_balance = 0.0
    closing_balance = 0.0
    supplier = None

    if supplier_id:
        supplier = Supplier.query.get(supplier_id)
        if supplier:
            opening_balance = supplier.previous_balance
            closing_balance = supplier.current_balance
            # Transactions will go here in the future
            ledger_data = []

    return render_template('supplier_ledger.html', suppliers=suppliers, ledger_data=ledger_data, 
                           opening_balance=opening_balance, closing_balance=closing_balance, supplier=supplier,
                           from_date=from_date, to_date=to_date)

@login_required
@supplier_bp.route('/supplier_due_list')
def supplier_due_list():
    suppliers = Supplier.query.filter(Supplier.current_balance > 0).all()
    total_due = sum(s.current_balance for s in suppliers)
    return render_template('supplier_due_list.html', suppliers=suppliers, total_due=total_due)
