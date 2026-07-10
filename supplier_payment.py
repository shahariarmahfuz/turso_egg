from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from auth import admin_required, current_user
from models import db, SupplierPayment, Supplier, SupplierLedger, CashLedger, dhaka_now
from datetime import datetime

supplier_payment_bp = Blueprint('supplier_payment', __name__, url_prefix='/supplier_payment')

@supplier_payment_bp.route('/api/get_supplier_due/<int:supplier_id>')
@login_required
def get_supplier_due(supplier_id):
    supplier = Supplier.query.get(supplier_id)
    if not supplier: return jsonify({'due': 0})
    return jsonify({'due': supplier.current_balance})

@supplier_payment_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        try:
            supplier_id = request.form.get('supplier_id')
            date_str = request.form.get('date')
            payment_method = request.form.get('payment_method')
            discount = float(request.form.get('discount') or 0)
            cash_paid = float(request.form.get('cash_paid') or 0)
            bank_name = request.form.get('bank_name')
            cheque_number = request.form.get('cheque_number')
            note = request.form.get('note')
            
            supplier = Supplier.query.get(supplier_id)
            if not supplier:
                flash("Supplier not found.", "danger")
                return redirect(url_for('supplier_payment.payment'))
                
            previous_due = supplier.current_balance
            
            balance = previous_due - discount - cash_paid
            
            payment_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else dhaka_now().date()
            
            col = SupplierPayment(
                supplier_id=supplier_id,
                date=payment_date,
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
            
            supplier.current_balance = balance
            
            # Supplier Ledger (Credit)
            c_ledger = SupplierLedger(
                supplier_id=supplier_id,
                date=payment_date,
                invoice_no=col.voucher_no,
                description=f"Payment ({payment_method})",
                debit=cash_paid + discount,
                balance=supplier.current_balance
            )
            db.session.add(c_ledger)
            
            # Cash Ledger (In)
            if cash_paid > 0:
                # get last cash ledger to calc running balance
                last_cash = CashLedger.query.order_by(CashLedger.id.desc()).first()
                running = last_cash.running_balance if last_cash else 0.0
                new_running = running - cash_paid
                
                cash_lg = CashLedger(
                    voucher_no=col.voucher_no,
                    description=f"Supplier Payment to {supplier.supplier_name}",
                    amount=cash_paid,
                    type='Out',
                    date=payment_date,
                    running_balance=new_running
                )
                db.session.add(cash_lg)

            db.session.commit()
            flash("Payment saved successfully!", "success")
            return redirect(url_for('supplier_payment.manage_payment'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving payment: {e}", "danger")
            return redirect(url_for('supplier_payment.payment'))
            
            
    pre_supplier_id = request.args.get('supplier_id')
    pre_supplier = Supplier.query.get(pre_supplier_id) if pre_supplier_id else None
    return render_template('payment_form.html', action="Add", pre_supplier=pre_supplier)

@supplier_payment_bp.route('/manage_payment')
@login_required
def manage_payment():
    payments = SupplierPayment.query.order_by(SupplierPayment.date.desc(), SupplierPayment.id.desc()).all()
    return render_template('manage_payment.html', payments=payments)

@supplier_payment_bp.route('/delete_payment/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_payment(id):
    try:
        col = SupplierPayment.query.get_or_404(id)
        
        # Restore supplier due
        amount_to_restore = col.cash_paid + col.discount
        col.supplier.current_balance += amount_to_restore
        
        # Remove SupplierLedger manually
        ledgers = SupplierLedger.query.filter_by(invoice_no=col.voucher_no).all()
        for lg in ledgers:
            db.session.delete(lg)
            
        # Revert Cash Ledger and update all subsequent cash ledgers
        cash_lg = CashLedger.query.filter_by(voucher_no=col.voucher_no).first()
        if cash_lg:
            amount_to_deduct = cash_lg.amount
            subsequent_cash = CashLedger.query.filter(CashLedger.id > cash_lg.id).all()
            for sc in subsequent_cash:
                sc.running_balance += amount_to_deduct
            db.session.delete(cash_lg)

        db.session.delete(col)
        db.session.commit()
        flash("Payment deleted and balances restored.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting payment: {e}", "danger")
        
    return redirect(url_for('supplier_payment.manage_payment'))

@supplier_payment_bp.route('/payments_report')
@login_required
def payments_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    supplier_id = request.args.get('supplier_id')
    voucher_no = request.args.get('voucher_no')
    payment_method = request.args.get('payment_method')
    
    query = SupplierPayment.query
    
    if from_date:
        query = query.filter(SupplierPayment.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(SupplierPayment.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if supplier_id:
        query = query.filter(SupplierPayment.supplier_id == supplier_id)
    if voucher_no:
        query = query.filter(SupplierPayment.voucher_no.like(f"%{voucher_no}%"))
    if payment_method:
        query = query.filter(SupplierPayment.payment_method == payment_method)
        
    payments = query.order_by(SupplierPayment.date.desc()).all()
    
    totals = {'prev_due': 0, 'discount': 0, 'cash_paid': 0, 'cheque': 0, 'balance': 0}
    for c in payments:
        totals['prev_due'] += c.previous_due
        totals['discount'] += c.discount
        totals['cash_paid'] += c.cash_paid if c.payment_method != 'Cheque' else 0
        totals['cheque'] += c.cash_paid if c.payment_method == 'Cheque' else 0
        totals['balance'] += c.balance
        
    suppliers = Supplier.query.order_by(Supplier.supplier_name).all()
    return render_template('payments_report.html', payments=payments, totals=totals, suppliers=suppliers,
                           from_date=from_date, to_date=to_date, supplier_id=supplier_id, 
                           voucher_no=voucher_no, payment_method=payment_method)
