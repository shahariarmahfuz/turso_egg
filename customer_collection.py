from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from auth import admin_required, current_user
from models import db, CustomerCollection, Customer, CustomerLedger, CashLedger, Sale, SaleReturn, dhaka_now
from datetime import datetime
from sqlalchemy import func

customer_collection_bp = Blueprint('customer_collection', __name__, url_prefix='/customer_collection')


def _calculate_customer_due(customer_id):
    """
    Dynamically compute a customer's actual outstanding due from all
    completed transactions, instead of relying on the stored current_balance.

    Formula:
        Opening Balance (previous_balance)
      + Total Sale Dues           (sum of Sale.due_amount)
      - Total Sale Return Credits (sum of SaleReturn subtotal - discount)
      - Total Collection Paid     (sum of CustomerCollection.cash_paid)
      - Total Collection Discount (sum of CustomerCollection.discount)
      = Current Outstanding Due
    """
    customer = Customer.query.get(customer_id)
    if not customer:
        return 0.0, None

    opening = customer.previous_balance or 0.0

    # Total due from sales (only the due portion — cash_paid at sale time is already settled)
    total_sale_due = db.session.query(
        func.coalesce(func.sum(Sale.due_amount), 0.0)
    ).filter(Sale.customer_id == customer_id).scalar()

    # Total credit from sale returns (subtotal - discount = total_amount returned)
    total_return_credit = db.session.query(
        func.coalesce(func.sum(SaleReturn.subtotal - SaleReturn.discount), 0.0)
    ).filter(SaleReturn.customer_id == customer_id).scalar()

    # Total collected (cash_paid + discount) from customer collections
    total_collected_paid = db.session.query(
        func.coalesce(func.sum(CustomerCollection.cash_paid), 0.0)
    ).filter(CustomerCollection.customer_id == customer_id).scalar()

    total_collected_discount = db.session.query(
        func.coalesce(func.sum(CustomerCollection.discount), 0.0)
    ).filter(CustomerCollection.customer_id == customer_id).scalar()

    computed_due = (
        opening
        + float(total_sale_due)
        - float(total_return_credit)
        - float(total_collected_paid)
        - float(total_collected_discount)
    )

    # Avoid tiny floating-point anomalies like -0.0
    if abs(computed_due) < 0.005:
        computed_due = 0.0

    return round(computed_due, 2), customer


@customer_collection_bp.route('/api/get_customer_due/<int:customer_id>')
@login_required
def get_customer_due(customer_id):
    computed_due, customer = _calculate_customer_due(customer_id)
    if not customer:
        return jsonify({'due': 0, 'total_collected': 0})

    # Sync stored current_balance if it drifted out of sync
    if abs((customer.current_balance or 0) - computed_due) > 0.005:
        customer.current_balance = computed_due
        db.session.commit()

    # Also return total collections received for display
    total_collected = db.session.query(
        func.coalesce(func.sum(CustomerCollection.cash_paid), 0.0)
    ).filter(CustomerCollection.customer_id == customer_id).scalar()

    return jsonify({
        'due': computed_due,
        'total_collected': round(float(total_collected), 2)
    })

@customer_collection_bp.route('/collection', methods=['GET', 'POST'])
@login_required
def collection():
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            date_str = request.form.get('date')
            payment_method = request.form.get('payment_method')
            discount = float(request.form.get('discount') or 0)
            cash_paid = float(request.form.get('cash_paid') or 0)
            bank_name = request.form.get('bank_name')
            cheque_number = request.form.get('cheque_number')
            note = request.form.get('note')
            
            customer = Customer.query.get(customer_id)
            if not customer:
                flash("Customer not found.", "danger")
                return redirect(url_for('customer_collection.collection'))
                
            # Use dynamically computed due instead of stored current_balance
            previous_due, _ = _calculate_customer_due(customer_id)
            
            # Allow negative balance for advance payments
            balance = previous_due - discount - cash_paid
            
            collection_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else dhaka_now().date()
            
            col = CustomerCollection(
                customer_id=customer_id,
                date=collection_date,
                previous_due=previous_due,
                discount=discount,
                cash_paid=cash_paid,
                balance=balance,
                payment_method=payment_method,
                bank_name=bank_name if payment_method in ['Bank', 'Cheque'] else None,
                cheque_number=cheque_number if payment_method in ['Cheque'] else None,
                note=note,
                created_by=current_user.id
            )
            
            db.session.add(col)
            db.session.flush() # Get voucher_no
            
            customer.current_balance = balance
            
            # Customer Ledger (Credit)
            c_ledger = CustomerLedger(
                customer_id=customer_id,
                date=collection_date,
                invoice_no=col.voucher_no,
                description=f"Collection ({payment_method})",
                credit=cash_paid + discount,
                balance=customer.current_balance
            )
            db.session.add(c_ledger)
            
            # Cash Ledger (In)
            if cash_paid > 0:
                # get last cash ledger to calc running balance
                last_cash = CashLedger.query.order_by(CashLedger.id.desc()).first()
                running = last_cash.running_balance if last_cash else 0.0
                new_running = running + cash_paid
                
                cash_lg = CashLedger(
                    voucher_no=col.voucher_no,
                    description=f"Customer Collection from {customer.customer_name}",
                    amount=cash_paid,
                    type='In',
                    date=collection_date,
                    running_balance=new_running
                )
                db.session.add(cash_lg)

            db.session.commit()
            flash("Collection saved successfully!", "success")
            return redirect(url_for('customer_collection.manage_collection'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving collection: {e}", "danger")
            return redirect(url_for('customer_collection.collection'))
            
    return render_template('collection_form.html', action="Add")

@customer_collection_bp.route('/manage_collection')
@login_required
def manage_collection():
    collections = CustomerCollection.query.order_by(CustomerCollection.date.desc(), CustomerCollection.id.desc()).all()
    return render_template('manage_collection.html', collections=collections)

@customer_collection_bp.route('/edit_collection/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_collection(id):
    col = CustomerCollection.query.get_or_404(id)
    customer = col.customer
    
    if request.method == 'POST':
        try:
            # Concurrency check
            submitted_updated_at_str = request.form.get('last_updated_at', '')
            col_updated_at_str = str(col.updated_at or col.created_at)
            
            if submitted_updated_at_str != col_updated_at_str:
                flash("Error: This collection was modified by another user while you were editing. Please refresh and try again.", "danger")
                return redirect(url_for('customer_collection.edit_collection', id=col.id))
            
            date_str = request.form.get('date')
            new_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else col.date
            
            payment_method = request.form.get('payment_method')
            discount = float(request.form.get('discount') or 0)
            cash_paid = float(request.form.get('cash_paid') or 0)
            bank_name = request.form.get('bank_name')
            cheque_number = request.form.get('cheque_number')
            note = request.form.get('note')
            
            old_date = col.date
            old_cash_paid = col.cash_paid
            old_discount = col.discount
            
            if old_date == new_date and old_cash_paid == cash_paid and old_discount == discount and col.payment_method == payment_method and col.note == note and col.bank_name == bank_name and col.cheque_number == cheque_number:
                flash("No changes detected.", "info")
                return redirect(url_for('customer_collection.manage_collection'))
            
            earliest_date = min(old_date, new_date)
            
            col.date = new_date
            col.discount = discount
            col.cash_paid = cash_paid
            col.payment_method = payment_method
            col.bank_name = bank_name if payment_method in ['Bank', 'Cheque'] else None
            col.cheque_number = cheque_number if payment_method in ['Cheque'] else None
            col.note = note
            col.updated_by = current_user.id
            col.updated_at = dhaka_now()
            
            c_ledger = CustomerLedger.query.filter_by(invoice_no=col.voucher_no).first()
            if c_ledger:
                c_ledger.date = new_date
                c_ledger.credit = cash_paid + discount
                c_ledger.description = f"Collection ({payment_method})"
            
            cash_lg = CashLedger.query.filter_by(voucher_no=col.voucher_no).first()
            if cash_lg:
                if cash_paid == 0:
                    db.session.delete(cash_lg)
                else:
                    cash_lg.date = new_date
                    cash_lg.amount = cash_paid
                    cash_lg.description = f"Customer Collection from {customer.customer_name}"
            elif cash_paid > 0:
                new_cash_lg = CashLedger(
                    voucher_no=col.voucher_no,
                    description=f"Customer Collection from {customer.customer_name}",
                    amount=cash_paid,
                    type='In',
                    date=new_date,
                    running_balance=0.0
                )
                db.session.add(new_cash_lg)
                
            db.session.flush()
            
            # --- CashLedger Forward Rebuild ---
            baseline_cash = CashLedger.query.filter(CashLedger.date < earliest_date).order_by(CashLedger.date.desc(), CashLedger.id.desc()).first()
            current_cash = baseline_cash.running_balance if baseline_cash else 0.0
            
            subsequent_cash = CashLedger.query.filter(CashLedger.date >= earliest_date).order_by(CashLedger.date.asc(), CashLedger.id.asc()).all()
            for sc in subsequent_cash:
                if sc.type == 'In':
                    current_cash += sc.amount
                elif sc.type == 'Out':
                    current_cash -= sc.amount
                sc.running_balance = current_cash
                
            # --- CustomerLedger Forward Rebuild ---
            baseline_cust = CustomerLedger.query.filter(
                CustomerLedger.customer_id == customer.id,
                CustomerLedger.date < earliest_date
            ).order_by(CustomerLedger.date.desc(), CustomerLedger.id.desc()).first()
            
            current_due = baseline_cust.balance if baseline_cust else (customer.previous_balance or 0.0)
            
            subsequent_cust = CustomerLedger.query.filter(
                CustomerLedger.customer_id == customer.id,
                CustomerLedger.date >= earliest_date
            ).order_by(CustomerLedger.date.asc(), CustomerLedger.id.asc()).all()
            
            for sc in subsequent_cust:
                current_due = current_due + sc.debit - sc.credit
                sc.balance = current_due

            db.session.commit()
            
            computed_due, _ = _calculate_customer_due(customer.id)
            customer.current_balance = computed_due
            db.session.commit()
            
            flash("Collection updated successfully!", "success")
            return redirect(url_for('customer_collection.manage_collection'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating collection: {e}", "danger")
            return redirect(url_for('customer_collection.edit_collection', id=col.id))
            
    return render_template('collection_form.html', action="Edit", collection=col)

@customer_collection_bp.route('/delete_collection/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_collection(id):
    try:
        col = CustomerCollection.query.get_or_404(id)
        customer = col.customer
        
        # Remove CustomerLedger manually
        ledgers = CustomerLedger.query.filter_by(invoice_no=col.voucher_no).all()
        for lg in ledgers:
            db.session.delete(lg)
            
        # Revert Cash Ledger and update all subsequent cash ledgers
        cash_lg = CashLedger.query.filter_by(voucher_no=col.voucher_no).first()
        if cash_lg:
            amount_to_deduct = cash_lg.amount
            subsequent_cash = CashLedger.query.filter(CashLedger.id > cash_lg.id).all()
            for sc in subsequent_cash:
                sc.running_balance -= amount_to_deduct
            db.session.delete(cash_lg)

        db.session.delete(col)
        db.session.flush()

        # Recalculate and sync customer balance from transaction history
        computed_due, _ = _calculate_customer_due(customer.id)
        customer.current_balance = computed_due

        db.session.commit()
        flash("Collection deleted and balances restored.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting collection: {e}", "danger")
        
    return redirect(url_for('customer_collection.manage_collection'))

@customer_collection_bp.route('/collections_report')
@login_required
def collections_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    customer_id = request.args.get('customer_id')
    voucher_no = request.args.get('voucher_no')
    payment_method = request.args.get('payment_method')
    
    query = CustomerCollection.query
    
    if from_date:
        query = query.filter(CustomerCollection.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(CustomerCollection.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if customer_id:
        query = query.filter(CustomerCollection.customer_id == customer_id)
    if voucher_no:
        query = query.filter(CustomerCollection.voucher_no.like(f"%{voucher_no}%"))
    if payment_method:
        query = query.filter(CustomerCollection.payment_method == payment_method)
        
    collections = query.order_by(CustomerCollection.date.desc()).all()
    
    totals = {'prev_due': 0, 'discount': 0, 'cash_paid': 0, 'cheque': 0, 'balance': 0}
    for c in collections:
        totals['prev_due'] += c.previous_due
        totals['discount'] += c.discount
        totals['cash_paid'] += c.cash_paid if c.payment_method != 'Cheque' else 0
        totals['cheque'] += c.cash_paid if c.payment_method == 'Cheque' else 0
        totals['balance'] += c.balance
        
    customers = Customer.query.order_by(Customer.customer_name).all()
    return render_template('collections_report.html', collections=collections, totals=totals, customers=customers,
                           from_date=from_date, to_date=to_date, customer_id=customer_id, 
                           voucher_no=voucher_no, payment_method=payment_method)
