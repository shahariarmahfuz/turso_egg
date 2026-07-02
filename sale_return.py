from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from auth import admin_required, current_user
from models import db, SaleReturn, SaleReturnItem, Customer, Product, CustomerLedger, Sale, SaleItem
from datetime import datetime

sale_return_bp = Blueprint('sale_return', __name__, url_prefix='/sale_return')

@sale_return_bp.route('/api/get_sales/<int:customer_id>')
@login_required
def get_sales(customer_id):
    sales = Sale.query.filter_by(customer_id=customer_id).all()
    result = [{'invoice_no': s.invoice_no, 'date': s.sale_date.strftime('%Y-%m-%d')} for s in sales]
    return jsonify(result)

@sale_return_bp.route('/api/get_sale_items/<invoice_no>')
@login_required
def get_sale_items(invoice_no):
    sale = Sale.query.filter_by(invoice_no=invoice_no).first()
    if not sale: return jsonify([])
    
    result = []
    for item in sale.items:
        # Calculate already returned quantity
        returned_qty = 0
        returns = SaleReturn.query.filter_by(sale_invoice=invoice_no).all()
        for r in returns:
            for r_item in r.items:
                if r_item.product_id == item.product_id:
                    returned_qty += r_item.quantity
        
        remaining = item.quantity - returned_qty
        if remaining > 0:
            result.append({
                'product_id': item.product_id,
                'code': item.product.product_code,
                'name': item.product.product_name,
                'sale_price': item.selling_price,
                'sold_qty': item.quantity,
                'returned_qty': returned_qty,
                'remaining_qty': remaining,
                'stock': item.product.current_stock
            })
    return jsonify(result)

@sale_return_bp.route('/add_sale_return', methods=['GET', 'POST'])
@login_required
def add_sale_return():
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            sale_invoice = request.form.get('sale_invoice')
            date_str = request.form.get('date')
            payment_method = request.form.get('payment_method')
            discount = float(request.form.get('discount') or 0)
            cash_paid = float(request.form.get('cash_paid') or 0)
            note = request.form.get('note')
            
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            
            if not product_ids:
                flash('Please add at least one product to return.', 'danger')
                return redirect(url_for('sale_return.add_sale_return'))
                
            customer = Customer.query.get(customer_id)
            if not customer:
                flash('Customer not found.', 'danger')
                return redirect(url_for('sale_return.add_sale_return'))

            return_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
            
            new_return = SaleReturn(
                sale_invoice=sale_invoice,
                customer_id=customer_id,
                date=return_date,
                discount=discount,
                paid=cash_paid,
                payment_method=payment_method,
                note=note,
                created_by=current_user.id
            )
            
            subtotal = 0
            for i in range(len(product_ids)):
                pid = int(product_ids[i])
                qty = float(quantities[i])
                price = float(prices[i])
                total = qty * price
                subtotal += total
                
                if qty <= 0: continue
                
                ritem = SaleReturnItem(
                    product_id=pid,
                    quantity=qty,
                    price=price,
                    total=total
                )
                new_return.items.append(ritem)
                
                # Increase Stock
                prod = Product.query.get(pid)
                prod.current_stock += qty
            
            new_return.subtotal = subtotal
            total_amount = subtotal - discount
            due = total_amount - cash_paid
            if due < 0: due = 0
            new_return.due = due
            
            db.session.add(new_return)
            db.session.flush() # To get return_invoice
            
            # Reduce Customer Due (Return is a credit to customer)
            customer.current_balance -= total_amount
            
            # Ledger Entry (Credit)
            ledger = CustomerLedger(
                customer_id=customer_id,
                date=return_date,
                invoice_no=new_return.return_invoice,
                description=f"Sale Return ({sale_invoice})",
                credit=total_amount,
                balance=customer.current_balance
            )
            db.session.add(ledger)
            
            db.session.commit()
            flash('Sale Return processed successfully!', 'success')
            return redirect(url_for('sale_return.manage_sale_return'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('sale_return.add_sale_return'))

    customers = Customer.query.order_by(Customer.customer_name).all()
    return render_template('add_sale_return.html', customers=customers, action="Add")

@sale_return_bp.route('/manage_sale_return')
@login_required
def manage_sale_return():
    returns = SaleReturn.query.order_by(SaleReturn.date.desc(), SaleReturn.id.desc()).all()
    return render_template('manage_sale_return.html', returns=returns)

@sale_return_bp.route('/delete_sale_return/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_sale_return(id):
    try:
        sr = SaleReturn.query.get_or_404(id)
        
        # Revert Stock
        for item in sr.items:
            item.product.current_stock -= item.quantity
            
        # Revert Customer Balance
        total_amount = sr.subtotal - sr.discount
        sr.customer.current_balance += total_amount
        
        # The cascade will delete items and CustomerLedger if backref cascade is properly set?
        # Actually customer ledger needs manual delete or explicit query
        ledgers = CustomerLedger.query.filter_by(invoice_no=sr.return_invoice).all()
        for lg in ledgers:
            db.session.delete(lg)
            
        db.session.delete(sr)
        db.session.commit()
        flash('Sale Return deleted and balances restored.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting return: {str(e)}', 'danger')
        
    return redirect(url_for('sale_return.manage_sale_return'))

@sale_return_bp.route('/sale_return_report')
@login_required
def sale_return_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    customer_id = request.args.get('customer_id')
    invoice_no = request.args.get('invoice_no')
    
    query = SaleReturn.query
    
    if from_date:
        query = query.filter(SaleReturn.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(SaleReturn.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if customer_id:
        query = query.filter(SaleReturn.customer_id == customer_id)
    if invoice_no:
        query = query.filter(SaleReturn.return_invoice.like(f"%{invoice_no}%"))
        
    returns = query.order_by(SaleReturn.date.desc()).all()
    
    totals = {'total': 0, 'discount': 0, 'paid': 0, 'due': 0}
    for r in returns:
        totals['total'] += r.subtotal
        totals['discount'] += r.discount
        totals['paid'] += r.paid
        totals['due'] += r.due
        
    customers = Customer.query.order_by(Customer.customer_name).all()
    return render_template('sale_return_report.html', returns=returns, totals=totals, customers=customers,
                           from_date=from_date, to_date=to_date, customer_id=customer_id, invoice_no=invoice_no)
