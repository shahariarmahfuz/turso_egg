from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from auth import admin_required
from models import db, Sale, SaleItem, Customer, Product, CustomerLedger, CashLedger, dhaka_now
from datetime import datetime

sale_bp = Blueprint('sale', __name__, url_prefix='/sale')

@login_required
@sale_bp.route('/add_sale', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            bill_number = request.form.get('bill_number')
            sale_date_str = request.form.get('sale_date')
            payment_method = request.form.get('payment_method')
            
            transport_cost = float(request.form.get('transport_cost') or 0.0)
            labour_cost = float(request.form.get('labour_cost') or 0.0)
            vat = float(request.form.get('vat') or 0.0)
            discount = float(request.form.get('discount') or 0.0)
            cash_paid = float(request.form.get('cash_paid') or 0.0)
            note = request.form.get('note')

            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')

            if not product_ids:
                flash("At least one product is required.", "danger")
                return redirect(url_for('sale.add_sale'))

            if not customer_id:
                cash_cust = Customer.query.filter_by(customer_name='Cash Customer').first()
                if not cash_cust:
                    cash_cust = Customer(customer_name='Cash Customer', contact_number='N/A')
                    db.session.add(cash_cust)
                    db.session.flush()
                customer_id = cash_cust.id
                is_cash_sale = True
            else:
                is_cash_sale = False

            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date() if sale_date_str else dhaka_now().date()
            
            subtotal = 0.0
            for qty, price in zip(quantities, prices):
                subtotal += float(qty) * float(price)
                
            total_amount = subtotal + transport_cost + labour_cost + vat - discount
            due_amount = total_amount - cash_paid
            if due_amount < 0: due_amount = 0
            
            # Start transaction
            new_sale = Sale(
                customer_id=customer_id,
                sale_date=sale_date,
                bill_number=bill_number,
                transport_cost=transport_cost,
                labour_cost=labour_cost,
                vat=vat,
                discount=discount,
                subtotal=subtotal,
                total_amount=total_amount,
                cash_paid=cash_paid,
                due_amount=due_amount,
                payment_method=payment_method,
                note=note
            )
            db.session.add(new_sale)
            db.session.flush()
            
            for p_id, qty, price in zip(product_ids, quantities, prices):
                qty_f = float(qty)
                price_f = float(price)
                prod = Product.query.get(p_id)
                cost = prod.cost_price if prod else 0.0
                profit = (price_f - cost) * qty_f
                
                item = SaleItem(
                    sale_id=new_sale.id,
                    product_id=p_id,
                    quantity=qty_f,
                    selling_price=price_f,
                    cost_price=cost,
                    profit=profit,
                    total_price=qty_f * price_f
                )
                db.session.add(item)
                
                # Update stock
                if prod:
                    prod.current_stock -= qty_f
            
            # Update Customer Due and Ledger
            if not is_cash_sale:
                cust = Customer.query.get(customer_id)
                if cust:
                    cust.current_balance += due_amount
                    
                    if due_amount > 0 or total_amount > 0:
                        ledger_desc = f"Sale Invoice: {new_sale.invoice_no}"
                        ledger = CustomerLedger(
                            customer_id=cust.id,
                            date=sale_date,
                            invoice_no=new_sale.invoice_no,
                            description=ledger_desc,
                            debit=total_amount,
                            credit=cash_paid,
                            balance=cust.current_balance
                        )
                        db.session.add(ledger)
            
            # Insert into CashLedger for cash_paid
            if cash_paid > 0:
                from models import CashLedger
                last_cash = CashLedger.query.order_by(CashLedger.id.desc()).first()
                running = last_cash.running_balance if last_cash else 0.0
                new_running = running + cash_paid
                cash_lg = CashLedger(
                    voucher_no=new_sale.invoice_no,
                    description="Sale Product in Cash",
                    amount=cash_paid,
                    type='In',
                    date=sale_date,
                    running_balance=new_running
                )
                db.session.add(cash_lg)

            db.session.commit()
            flash("Sale completed successfully.", "success")
            return redirect(url_for('sale.manage_sale'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving sale: {e}", "danger")

    return render_template('sale_form.html', action="Add")


@sale_bp.route('/api/get_customer/<int:customer_id>')
@login_required
def get_customer(customer_id):
    cust = Customer.query.get(customer_id)
    if cust:
        return jsonify({'address': cust.address, 'contact': cust.contact_number})
    return jsonify({'address': '', 'contact': ''})

@sale_bp.route('/api/search_product')
@login_required
def search_product():
    term = request.args.get('q', '')
    if not term:
        return jsonify([])
    # Support barcode / product_code / product_name search
    prods = Product.query.filter(
        db.or_(
            Product.product_code.ilike(f'%{term}%'),
            Product.product_name.ilike(f'%{term}%'),
            Product.barcode.ilike(f'%{term}%')
        ),
        Product.status == 'Active'
    ).limit(10).all()
    results = [{'id': p.id, 'text': f"{p.product_name} ({p.product_code}) - Stock: {p.current_stock}", 'code': p.product_code, 'name': p.product_name, 'stock': p.current_stock, 'price': p.selling_price} for p in prods]
    return jsonify(results)

@login_required
@admin_required
@sale_bp.route('/edit_sale/<int:id>', methods=['GET', 'POST'])
def edit_sale(id):
    sale = Sale.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            bill_number = request.form.get('bill_number')
            sale_date_str = request.form.get('sale_date')
            payment_method = request.form.get('payment_method')
            
            transport_cost = float(request.form.get('transport_cost') or 0.0)
            labour_cost = float(request.form.get('labour_cost') or 0.0)
            vat = float(request.form.get('vat') or 0.0)
            discount = float(request.form.get('discount') or 0.0)
            cash_paid = float(request.form.get('cash_paid') or 0.0)
            note = request.form.get('note')

            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')

            if not product_ids:
                flash("At least one product is required.", "danger")
                return redirect(url_for('sale.edit_sale', id=id))

            if not customer_id:
                cash_cust = Customer.query.filter_by(customer_name='Cash Customer').first()
                if not cash_cust:
                    cash_cust = Customer(customer_name='Cash Customer', contact_number='N/A')
                    db.session.add(cash_cust)
                    db.session.flush()
                customer_id = cash_cust.id
                is_cash_sale = True
            else:
                is_cash_sale = False
                
            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date() if sale_date_str else sale.sale_date
            
            subtotal = 0.0
            for qty, price in zip(quantities, prices):
                subtotal += float(qty) * float(price)
                
            total_amount = subtotal + transport_cost + labour_cost + vat - discount
            due_amount = total_amount - cash_paid
            if due_amount < 0: due_amount = 0

            # Revert original sale effects
            for item in sale.items:
                prod = Product.query.get(item.product_id)
                if prod:
                    prod.current_stock += item.quantity
                db.session.delete(item)
                
            old_cust = Customer.query.get(sale.customer_id)
            if old_cust:
                old_cust.current_balance -= sale.due_amount
                
            # Cash Ledger Logic (Updating instead of deleting to preserve IDs and running balances)
            cash_lg = CashLedger.query.filter_by(voucher_no=sale.invoice_no).first()
            if cash_paid > 0:
                if cash_lg:
                    diff = cash_paid - cash_lg.amount
                    print(f"DEBUG: cash_paid={cash_paid}, cash_lg.amount={cash_lg.amount}, diff={diff}", flush=True)
                    if diff != 0:
                        cash_lg.amount = cash_paid
                        cash_lg.date = sale_date
                        cash_lg.running_balance += diff
                        subsequent_cash = CashLedger.query.filter(CashLedger.id > cash_lg.id).all()
                        for sc in subsequent_cash:
                            sc.running_balance += diff
                else:
                    last_cash = CashLedger.query.order_by(CashLedger.id.desc()).first()
                    running = last_cash.running_balance if last_cash else 0.0
                    new_running = running + cash_paid
                    cash_lg = CashLedger(
                        voucher_no=sale.invoice_no,
                        description="Sale Product in Cash (Edited)",
                        amount=cash_paid,
                        type='In',
                        date=sale_date,
                        running_balance=new_running
                    )
                    db.session.add(cash_lg)
            else:
                if cash_lg:
                    amount_to_deduct = cash_lg.amount
                    subsequent_cash = CashLedger.query.filter(CashLedger.id > cash_lg.id).all()
                    for sc in subsequent_cash:
                        sc.running_balance -= amount_to_deduct
                    db.session.delete(cash_lg)

            db.session.flush()

            # Apply updated values to sale
            old_customer_id = sale.customer_id
            sale.customer_id = customer_id
            sale.sale_date = sale_date
            sale.bill_number = bill_number
            sale.transport_cost = transport_cost
            sale.labour_cost = labour_cost
            sale.vat = vat
            sale.discount = discount
            sale.subtotal = subtotal
            sale.total_amount = total_amount
            sale.cash_paid = cash_paid
            sale.due_amount = due_amount
            sale.payment_method = payment_method
            sale.note = note

            # Apply new effects
            for p_id, qty, price in zip(product_ids, quantities, prices):
                qty_f = float(qty)
                price_f = float(price)
                prod = Product.query.get(p_id)
                
                if prod:
                    if prod.current_stock - qty_f < 0:
                        raise ValueError(f"Stock for {prod.product_name} cannot be negative.")
                    prod.current_stock -= qty_f
                    
                cost = prod.cost_price if prod else 0.0
                profit = (price_f - cost) * qty_f
                
                new_item = SaleItem(
                    sale_id=sale.id,
                    product_id=p_id,
                    quantity=qty_f,
                    selling_price=price_f,
                    cost_price=cost,
                    profit=profit,
                    total_price=qty_f * price_f
                )
                db.session.add(new_item)
                
            # Customer Ledger Logic (Updating instead of deleting)
            if not is_cash_sale:
                new_cust = Customer.query.get(customer_id)
                if new_cust:
                    new_cust.current_balance += due_amount
                    
                    if old_customer_id == customer_id:
                        # Customer didn't change, update existing ledger
                        c_lg = CustomerLedger.query.filter_by(invoice_no=sale.invoice_no).first()
                        if c_lg:
                            c_lg.date = sale_date
                            c_lg.debit = total_amount
                            c_lg.credit = cash_paid
                            c_lg.balance = new_cust.current_balance
                        else:
                            if due_amount > 0 or total_amount > 0:
                                c_lg = CustomerLedger(
                                    customer_id=new_cust.id,
                                    date=sale_date,
                                    invoice_no=sale.invoice_no,
                                    description=f"Sale Invoice: {sale.invoice_no} (Edited)",
                                    debit=total_amount,
                                    credit=cash_paid,
                                    balance=new_cust.current_balance
                                )
                                db.session.add(c_lg)
                    else:
                        # Customer changed, delete old ledger and create new
                        c_lg_old = CustomerLedger.query.filter_by(invoice_no=sale.invoice_no, customer_id=old_customer_id).first()
                        if c_lg_old:
                            db.session.delete(c_lg_old)
                            
                        if due_amount > 0 or total_amount > 0:
                            c_lg_new = CustomerLedger(
                                customer_id=new_cust.id,
                                date=sale_date,
                                invoice_no=sale.invoice_no,
                                description=f"Sale Invoice: {sale.invoice_no} (Edited)",
                                debit=total_amount,
                                credit=cash_paid,
                                balance=new_cust.current_balance
                            )
                            db.session.add(c_lg_new)
            else:
                # Is a cash sale, ensure no customer ledger exists
                c_lg = CustomerLedger.query.filter_by(invoice_no=sale.invoice_no).first()
                if c_lg:
                    db.session.delete(c_lg)

            db.session.commit()
            flash("Sale updated successfully.", "success")
            return redirect(url_for('sale.manage_sale'))
        except ValueError as ve:
            db.session.rollback()
            print("VALUE_ERROR:", ve, flush=True)
            flash(str(ve), "danger")
            return redirect(url_for('sale.edit_sale', id=id))
        except Exception as e:
            db.session.rollback()
            print("EXCEPTION:", e, flush=True)
            flash(f"Error updating sale: {e}", "danger")
            return redirect(url_for('sale.edit_sale', id=id))

    return render_template('edit_sale.html', sale=sale, items=sale.items)

@login_required
@sale_bp.route('/manage_sale')
def manage_sale():
    sales = Sale.query.order_by(Sale.id.desc()).all()
    return render_template('manage_sale.html', sales=sales)

@login_required
@sale_bp.route('/delete_sale/<int:id>', methods=['POST'])
def delete_sale(id):
    sale = Sale.query.get_or_404(id)
    try:
        # Restore stock
        for item in sale.items:
            prod = Product.query.get(item.product_id)
            if prod:
                prod.current_stock += item.quantity
        
        # Restore customer balance
        cust = Customer.query.get(sale.customer_id)
        if cust:
            cust.current_balance -= sale.due_amount
            
        # Ledger entries deleted automatically by cascade delete-orphan if set up, or manual
        ledgers = CustomerLedger.query.filter_by(invoice_no=sale.invoice_no).all()
        for lg in ledgers:
            db.session.delete(lg)
            
        db.session.delete(sale)
        db.session.commit()
        flash("Sale deleted and stock/customer balances restored successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting sale: {e}", "danger")
    return redirect(url_for('sale.manage_sale'))

@login_required
@sale_bp.route('/sale_report')
def sale_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    invoice_no = request.args.get('invoice_no')
    customer_id = request.args.get('customer_id')

    if not from_date and not to_date:
        from_date = dhaka_now().strftime('%Y-%m-%d')
        to_date = dhaka_now().strftime('%Y-%m-%d')
    
    query = Sale.query
    if from_date:
        query = query.filter(Sale.sale_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(Sale.sale_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if invoice_no:
        query = query.filter(Sale.invoice_no.ilike(f"%{invoice_no}%"))
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)
        
    sales = query.order_by(Sale.sale_date.desc()).all()
    
    totals = {
        'total': sum(s.total_amount for s in sales),
        'vat': sum(s.vat for s in sales),
        'labour': sum(s.labour_cost for s in sales),
        'discount': sum(s.discount for s in sales),
        'paid': sum(s.cash_paid for s in sales),
        'due': sum(s.due_amount for s in sales),
        'profit': sum(sum(i.profit for i in s.items) for s in sales)
    }
    
    customers = Customer.query.all()
    return render_template('sale_report.html', sales=sales, totals=totals, 
                           from_date=from_date, to_date=to_date, invoice_no=invoice_no, 
                           customer_id=customer_id, customers=customers)

@login_required
@sale_bp.route('/sale_item_report')
def sale_item_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    customer_id = request.args.get('customer_id')
    
    query = SaleItem.query.join(Sale)
    if from_date:
        query = query.filter(Sale.sale_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(Sale.sale_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)
        
    items = query.order_by(Sale.sale_date.desc()).all()
    
    totals = {
        'qty': sum(i.quantity for i in items),
        'price': sum(i.total_price for i in items),
        'cost': sum(i.cost_price * i.quantity for i in items),
        'profit': sum(i.profit for i in items)
    }
    
    customers = Customer.query.all()
    return render_template('sale_item_report.html', items=items, totals=totals, customers=customers,
                           from_date=from_date, to_date=to_date, customer_id=customer_id)


@login_required
@sale_bp.route('/print_invoice/<int:id>')
def print_invoice(id):
    sale = Sale.query.get_or_404(id)
    return render_template('print_invoice.html', sale=sale)

@login_required
@sale_bp.route('/sale/<int:id>/truck-challan')
def print_truck_challan(id):
    sale = Sale.query.get_or_404(id)
    return render_template('print/truck_challan.html', sale=sale)
