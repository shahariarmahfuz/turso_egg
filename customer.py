from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import or_
from flask_login import login_required
from auth import admin_required
from models import db, Customer, CustomerLedger, dhaka_now
from datetime import datetime

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@login_required
@customer_bp.route('/search_customer', methods=['GET'])
def search_customer():
    q = request.args.get('q', '').strip()
    if not q:
        customers = Customer.query.limit(20).all()
    else:
        customers = Customer.query.filter(
            or_(
                Customer.customer_name.ilike(f'%{q}%'),
                Customer.customer_code.ilike(f'%{q}%'),
                Customer.contact_number.ilike(f'%{q}%')
            )
        ).limit(20).all()
    
    results = []
    for c in customers:
        results.append({
            'id': c.id,
            'text': f"{c.customer_name} ({c.contact_number or 'N/A'}) - {c.customer_code}"
        })
    return jsonify(results)

@login_required
@customer_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')
        previous_balance = request.form.get('previous_balance', 0.0)
        date_str = request.form.get('date')

        if not customer_name:
            flash("Customer Name is required.", "danger")
        else:
            try:
                prev_bal_val = float(previous_balance)
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else dhaka_now().date()
                
                new_cust = Customer(
                    customer_name=customer_name,
                    address=address,
                    contact_number=contact_number,
                    previous_balance=prev_bal_val,
                    current_balance=prev_bal_val,
                    created_date=date_obj
                )
                db.session.add(new_cust)
                db.session.flush() # To get the id
                
                # Add opening balance to ledger if there is one
                if prev_bal_val > 0:
                    ledger = CustomerLedger(
                        customer_id=new_cust.id,
                        date=date_obj,
                        description="Opening Balance",
                        debit=prev_bal_val,
                        balance=prev_bal_val
                    )
                    db.session.add(ledger)
                    
                db.session.commit()
                flash("Customer added successfully.", "success")
                return redirect(url_for('customer.manage_customer'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {e}", "danger")
            
    return render_template('customer_form.html', action="Add")

@login_required
@customer_bp.route('/manage_customer')
def manage_customer():
    customers = Customer.query.order_by(Customer.id.desc()).all()
    return render_template('manage_customer.html', customers=customers)

@login_required
@customer_bp.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    cust = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')
        previous_balance = request.form.get('previous_balance', 0.0)

        try:
            prev_bal_val = float(previous_balance)
            diff = prev_bal_val - cust.previous_balance
            cust.current_balance += diff
            cust.previous_balance = prev_bal_val
            cust.customer_name = customer_name
            cust.address = address
            cust.contact_number = contact_number
            db.session.commit()
            flash("Customer updated successfully.", "success")
            return redirect(url_for('customer.manage_customer'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
    return render_template('customer_form.html', action="Edit", customer=cust)

@login_required
@customer_bp.route('/delete_customer/<int:id>', methods=['POST'])
def delete_customer(id):
    cust = Customer.query.get_or_404(id)
    if cust.sales:
        flash("Cannot delete customer with sales history.", "danger")
    else:
        db.session.delete(cust)
        db.session.commit()
        flash("Customer deleted successfully.", "success")
    return redirect(url_for('customer.manage_customer'))

@login_required
@customer_bp.route('/customer_ledger', methods=['GET'])
def customer_ledger():
    customers = Customer.query.all()
    customer_id = request.args.get('customer_id')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    ledger_data = []
    opening_balance = 0.0
    closing_balance = 0.0
    customer = None

    if customer_id:
        customer = Customer.query.get(customer_id)
        if customer:
            opening_balance = customer.previous_balance
            closing_balance = customer.current_balance
            query = CustomerLedger.query.filter_by(customer_id=customer_id)
            if from_date:
                query = query.filter(CustomerLedger.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
            if to_date:
                query = query.filter(CustomerLedger.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
                
            ledger_data = query.order_by(CustomerLedger.date.asc(), CustomerLedger.id.asc()).all()

    return render_template('customer_ledger.html', customers=customers, ledger_data=ledger_data, 
                           opening_balance=opening_balance, closing_balance=closing_balance, customer=customer,
                           from_date=from_date, to_date=to_date)

@login_required
@customer_bp.route('/customer_due_list')
def customer_due_list():
    customers = Customer.query.filter(Customer.current_balance > 0).all()
    total_due = sum(c.current_balance for c in customers)
    return render_template('customer_due_list.html', customers=customers, total_due=total_due)
