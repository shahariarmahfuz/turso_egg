from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from auth import admin_required
from models import db, Purchase, PurchaseItem, Supplier, Product
from datetime import datetime

purchase_bp = Blueprint('purchase', __name__, url_prefix='/purchase')

@login_required
@purchase_bp.route('/add_purchase', methods=['GET', 'POST'])
def add_purchase():
    suppliers = Supplier.query.all()
    if request.method == 'POST':
        try:
            supplier_id = request.form.get('supplier_id')
            bill_number = request.form.get('bill_number')
            purchase_date_str = request.form.get('purchase_date')
            payment_method = request.form.get('payment_method')
            
            transport_cost = float(request.form.get('transport_cost') or 0.0)
            other_cost = float(request.form.get('other_cost') or 0.0)
            discount = float(request.form.get('discount') or 0.0)
            cash_paid = float(request.form.get('cash_paid') or 0.0)
            note = request.form.get('note')

            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')

            if not supplier_id or not product_ids:
                flash("Supplier and at least one product are required.", "danger")
                return redirect(url_for('purchase.add_purchase'))

            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else datetime.utcnow().date()
            
            subtotal = 0.0
            for qty, price in zip(quantities, prices):
                subtotal += float(qty) * float(price)
                
            total_amount = subtotal + transport_cost + other_cost - discount
            due_amount = total_amount - cash_paid
            
            # Start transaction
            new_purchase = Purchase(
                supplier_id=supplier_id,
                purchase_date=purchase_date,
                bill_number=bill_number,
                transport_cost=transport_cost,
                other_cost=other_cost,
                discount=discount,
                subtotal=subtotal,
                total_amount=total_amount,
                cash_paid=cash_paid,
                due_amount=due_amount,
                payment_method=payment_method,
                note=note
            )
            db.session.add(new_purchase)
            db.session.flush() # get new_purchase.id
            
            # Add Items & Update Stock
            for p_id, qty, price in zip(product_ids, quantities, prices):
                qty_f = float(qty)
                price_f = float(price)
                item = PurchaseItem(
                    purchase_id=new_purchase.id,
                    product_id=p_id,
                    quantity=qty_f,
                    purchase_price=price_f,
                    total_price=qty_f * price_f
                )
                db.session.add(item)
                
                # Update stock
                prod = Product.query.get(p_id)
                if prod:
                    prod.current_stock += qty_f
            
            # Update Supplier Due
            sup = Supplier.query.get(supplier_id)
            if sup and due_amount > 0:
                sup.current_balance += due_amount

            db.session.commit()
            flash("Purchase recorded successfully.", "success")
            return redirect(url_for('purchase.manage_purchase'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving purchase: {e}", "danger")

    return render_template('purchase_form.html', action="Add", suppliers=suppliers)


@purchase_bp.route('/api/get_supplier/<int:supplier_id>')
@login_required
def get_supplier(supplier_id):
    sup = Supplier.query.get(supplier_id)
    if sup:
        return jsonify({'address': sup.address, 'contact': sup.contact_number})
    return jsonify({'address': '', 'contact': ''})

@purchase_bp.route('/api/search_product')
@login_required
def search_product():
    term = request.args.get('q', '')
    if not term:
        return jsonify([])
    prods = Product.query.filter(db.or_(Product.product_code.ilike(f'%{term}%'), Product.product_name.ilike(f'%{term}%'))).limit(10).all()
    results = [{'id': p.id, 'text': f"{p.product_name} ({p.product_code}) - Stock: {p.current_stock}", 'code': p.product_code, 'name': p.product_name, 'stock': p.current_stock} for p in prods]
    return jsonify(results)

@login_required
@purchase_bp.route('/manage_purchase')
def manage_purchase():
    purchases = Purchase.query.order_by(Purchase.id.desc()).all()
    return render_template('manage_purchase.html', purchases=purchases)

@login_required
@purchase_bp.route('/delete_purchase/<int:id>', methods=['POST'])
def delete_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    try:
        # Restore stock
        for item in purchase.items:
            prod = Product.query.get(item.product_id)
            if prod:
                prod.current_stock -= item.quantity
        
        # Restore supplier balance
        if purchase.due_amount > 0:
            sup = Supplier.query.get(purchase.supplier_id)
            if sup:
                sup.current_balance -= purchase.due_amount
                
        db.session.delete(purchase)
        db.session.commit()
        flash("Purchase deleted and stock/supplier balances restored successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting purchase: {e}", "danger")
    return redirect(url_for('purchase.manage_purchase'))

@login_required
@purchase_bp.route('/purchase_report')
def purchase_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    invoice_no = request.args.get('invoice_no')
    
    query = Purchase.query
    if from_date:
        query = query.filter(Purchase.purchase_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(Purchase.purchase_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if invoice_no:
        query = query.filter(Purchase.invoice_no.ilike(f"%{invoice_no}%"))
        
    purchases = query.order_by(Purchase.purchase_date.desc()).all()
    
    totals = {
        'amount': sum(p.total_amount for p in purchases),
        'transport': sum(p.transport_cost for p in purchases),
        'other': sum(p.other_cost for p in purchases),
        'discount': sum(p.discount for p in purchases),
        'paid': sum(p.cash_paid for p in purchases),
        'due': sum(p.due_amount for p in purchases)
    }
    
    return render_template('purchase_report.html', purchases=purchases, totals=totals, 
                           from_date=from_date, to_date=to_date, invoice_no=invoice_no)

@login_required
@purchase_bp.route('/purchase_items_report')
def purchase_items_report():
    supplier_id = request.args.get('supplier_id')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    query = PurchaseItem.query.join(Purchase)
    if supplier_id:
        query = query.filter(Purchase.supplier_id == supplier_id)
    if from_date:
        query = query.filter(Purchase.purchase_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(Purchase.purchase_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
        
    items = query.order_by(Purchase.purchase_date.desc()).all()
    total_price = sum(i.total_price for i in items)
    
    suppliers = Supplier.query.all()
    
    return render_template('purchase_items_report.html', items=items, total_price=total_price, suppliers=suppliers,
                           supplier_id=supplier_id, from_date=from_date, to_date=to_date)
