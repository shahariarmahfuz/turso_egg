from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from auth import admin_required
from models import db, Purchase, PurchaseItem, Supplier, Product, PurchaseReturn, PurchaseReturnItem
from datetime import datetime

purchase_return_bp = Blueprint('purchase_return', __name__, url_prefix='/purchase_return')

@login_required
@purchase_return_bp.route('/add_purchase_return', methods=['GET', 'POST'])
def add_purchase_return():
    suppliers = Supplier.query.all()
    if request.method == 'POST':
        try:
            supplier_id = request.form.get('supplier_id')
            purchase_invoice = request.form.get('purchase_invoice')
            return_date_str = request.form.get('return_date')
            payment_method = request.form.get('payment_method')
            
            transport_cost = float(request.form.get('transport_cost') or 0.0)
            other_cost = float(request.form.get('other_cost') or 0.0)
            discount = float(request.form.get('discount') or 0.0)
            cash_refund = float(request.form.get('cash_refund') or 0.0)
            note = request.form.get('note')

            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')

            if not supplier_id or not product_ids:
                flash("Supplier and at least one product are required.", "danger")
                return redirect(url_for('purchase_return.add_purchase_return'))

            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date() if return_date_str else datetime.utcnow().date()
            
            subtotal = 0.0
            for qty, price in zip(quantities, prices):
                subtotal += float(qty) * float(price)
                
            total_amount = subtotal + transport_cost + other_cost - discount
            due_adjustment = total_amount - cash_refund
            
            purchase = Purchase.query.filter_by(invoice_no=purchase_invoice).first() if purchase_invoice else None
            purchase_id = purchase.id if purchase else None

            # Start transaction
            new_return = PurchaseReturn(
                purchase_id=purchase_id,
                supplier_id=supplier_id,
                return_date=return_date,
                transport_cost=transport_cost,
                other_cost=other_cost,
                discount=discount,
                subtotal=subtotal,
                total_amount=total_amount,
                cash_refund=cash_refund,
                due_adjustment=due_adjustment,
                payment_method=payment_method,
                note=note
            )
            db.session.add(new_return)
            db.session.flush()
            
            for p_id, qty, price in zip(product_ids, quantities, prices):
                qty_f = float(qty)
                price_f = float(price)
                item = PurchaseReturnItem(
                    return_id=new_return.id,
                    product_id=p_id,
                    quantity=qty_f,
                    purchase_price=price_f,
                    total_price=qty_f * price_f
                )
                db.session.add(item)
                
                # Update stock
                prod = Product.query.get(p_id)
                if prod:
                    prod.current_stock -= qty_f # Decrease stock for return to supplier
            
            # Update Supplier Due
            sup = Supplier.query.get(supplier_id)
            if sup and due_adjustment > 0:
                sup.current_balance -= due_adjustment # Reduce balance we owe them

            db.session.commit()
            flash("Purchase return recorded successfully.", "success")
            return redirect(url_for('purchase_return.manage_purchase_return'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving return: {e}", "danger")

    return render_template('purchase_return_form.html', action="Add", suppliers=suppliers)

@purchase_return_bp.route('/api/get_purchase/<invoice>')
@login_required
def get_purchase(invoice):
    purchase = Purchase.query.filter_by(invoice_no=invoice).first()
    if not purchase:
        return jsonify({'error': 'Invoice not found'})
    
    items = []
    for item in purchase.items:
        returned_qty = db.session.query(db.func.sum(PurchaseReturnItem.quantity)).join(PurchaseReturn).filter(PurchaseReturn.purchase_id==purchase.id, PurchaseReturnItem.product_id==item.product_id).scalar() or 0.0
        max_qty = item.quantity - returned_qty
        if max_qty > 0:
            items.append({
                'product_id': item.product_id,
                'code': item.product.product_code,
                'name': item.product.product_name,
                'max_qty': max_qty,
                'price': item.purchase_price,
                'stock': item.product.current_stock
            })

    return jsonify({
        'supplier_id': purchase.supplier_id,
        'items': items
    })

@login_required
@purchase_return_bp.route('/manage_purchase_return')
def manage_purchase_return():
    returns = PurchaseReturn.query.order_by(PurchaseReturn.id.desc()).all()
    return render_template('manage_purchase_return.html', returns=returns)

@login_required
@purchase_return_bp.route('/delete_purchase_return/<int:id>', methods=['POST'])
def delete_purchase_return(id):
    ret = PurchaseReturn.query.get_or_404(id)
    try:
        # Restore stock
        for item in ret.items:
            prod = Product.query.get(item.product_id)
            if prod:
                prod.current_stock += item.quantity # return to inventory
        
        # Restore supplier balance
        if ret.due_adjustment > 0:
            sup = Supplier.query.get(ret.supplier_id)
            if sup:
                sup.current_balance += ret.due_adjustment # Add debt back
                
        db.session.delete(ret)
        db.session.commit()
        flash("Purchase return deleted and stock/supplier balances restored successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting return: {e}", "danger")
    return redirect(url_for('purchase_return.manage_purchase_return'))

@login_required
@purchase_return_bp.route('/purchase_return_report')
def purchase_return_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    supplier_id = request.args.get('supplier_id')
    return_invoice = request.args.get('return_invoice')
    
    query = PurchaseReturn.query
    if from_date:
        query = query.filter(PurchaseReturn.return_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(PurchaseReturn.return_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if supplier_id:
        query = query.filter(PurchaseReturn.supplier_id == supplier_id)
    if return_invoice:
        query = query.filter(PurchaseReturn.return_invoice.ilike(f"%{return_invoice}%"))
        
    returns = query.order_by(PurchaseReturn.return_date.desc()).all()
    
    totals = {
        'amount': sum(r.total_amount for r in returns),
        'discount': sum(r.discount for r in returns),
        'refund': sum(r.cash_refund for r in returns),
        'adjustment': sum(r.due_adjustment for r in returns)
    }
    
    suppliers = Supplier.query.all()
    return render_template('purchase_return_report.html', returns=returns, totals=totals, 
                           from_date=from_date, to_date=to_date, supplier_id=supplier_id, return_invoice=return_invoice, suppliers=suppliers)
