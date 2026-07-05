import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import create_app
app = create_app()
from models import db, Business, Admin, Product, Customer, Sale, SaleItem, CustomerLedger, CashLedger
from datetime import date

def run_tests():
    with app.app_context():
        # Setup context
        # Find an existing business and admin for context
        biz = Business.query.first()
        admin = Admin.query.filter_by(role='Admin').first()
        if not admin:
            admin = Admin.query.first()
            
        print("Using Business:", biz.business_name)

        # 0. Setup Dummy Data
        # Delete if exist
        import random
        r_suffix = str(random.randint(1000, 9999))
        p1_code = f"TEST-P1-{r_suffix}"
        p2_code = f"TEST-P2-{r_suffix}"
        c1_code = f"C-TEST-1-{r_suffix}"
        c2_code = f"C-TEST-2-{r_suffix}"
        
        prod1 = Product(business_id=biz.id, product_code=p1_code, product_name="Product 1", cost_price=10, selling_price=15, current_stock=100)
        prod2 = Product(business_id=biz.id, product_code=p2_code, product_name="Product 2", cost_price=20, selling_price=30, current_stock=100)
        cust1 = Customer(business_id=biz.id, customer_code=c1_code, customer_name="Customer 1", current_balance=0)
        cust2 = Customer(business_id=biz.id, customer_code=c2_code, customer_name="Customer 2", current_balance=-50) # advance balance
        
        db.session.add_all([prod1, prod2, cust1, cust2])
        db.session.commit()
        
        # Get baseline cash ledger
        last_cash = CashLedger.query.order_by(CashLedger.id.desc()).first()
        baseline_cash_running = last_cash.running_balance if last_cash else 0.0

        print(f"Baseline Cash: {baseline_cash_running}")

        try:
            # Helper for creating a sale
            def create_sale(customer, items, cash_paid, discount=0):
                sale = Sale(
                    business_id=biz.id, customer_id=customer.id, sale_date=date.today(),
                    subtotal=sum(i['qty']*i['price'] for i in items),
                    discount=discount,
                    total_amount=sum(i['qty']*i['price'] for i in items) - discount,
                    cash_paid=cash_paid,
                    due_amount=max(0, sum(i['qty']*i['price'] for i in items) - discount - cash_paid),
                    payment_method='Cash' if cash_paid >= (sum(i['qty']*i['price'] for i in items)-discount) else 'Due'
                )
                db.session.add(sale)
                db.session.flush()
                for i in items:
                    si = SaleItem(sale_id=sale.id, product_id=i['prod'].id, quantity=i['qty'], selling_price=i['price'], cost_price=i['prod'].cost_price, profit=(i['price']-i['prod'].cost_price)*i['qty'], total_price=i['qty']*i['price'])
                    db.session.add(si)
                    i['prod'].current_stock -= i['qty']
                
                customer.current_balance += sale.due_amount
                
                if sale.due_amount > 0 or sale.total_amount > 0:
                    lg = CustomerLedger(customer_id=customer.id, date=sale.sale_date, invoice_no=sale.invoice_no, debit=sale.total_amount, credit=sale.cash_paid, balance=customer.current_balance)
                    db.session.add(lg)
                if cash_paid > 0:
                    lc = CashLedger.query.order_by(CashLedger.id.desc()).first()
                    rb = lc.running_balance if lc else 0.0
                    clg = CashLedger(voucher_no=sale.invoice_no, amount=cash_paid, type='In', date=sale.sale_date, running_balance=rb+cash_paid)
                    db.session.add(clg)
                db.session.commit()
                return sale.id
                
            from sale import edit_sale
            from flask import request
            
            def call_edit_sale_post(sale_id, customer_id, cash_paid, discount, product_ids, quantities, prices):
                with app.test_request_context(f'/business/{biz.business_slug}/sale/edit_sale/{sale_id}', method='POST', data={
                    'customer_id': customer_id,
                    'cash_paid': cash_paid,
                    'discount': discount,
                    'product_id[]': product_ids,
                    'quantity[]': quantities,
                    'price[]': prices,
                    'sale_date': date.today().strftime('%Y-%m-%d')
                }):
                    # Mock g.business and current_user
                    from flask import g
                    g.business = biz
                    g.business_slug = biz.business_slug
                    from flask_login import login_user
                    login_user(admin)
                    edit_sale(sale_id)

            # Scenario 1 & 2: Create a sale, then increase quantity, then decrease
            print("Running Scenarios 1 & 2: Edit Quantity...")
            s_id = create_sale(cust1, [{'prod': prod1, 'qty': 2, 'price': 15}], cash_paid=10) # total 30, paid 10, due 20
            call_edit_sale_post(s_id, cust1.id, 10, 0, [prod1.id], [3], [15]) # increase qty to 3, total 45, paid 10, due 35
            db.session.refresh(prod1)
            db.session.refresh(cust1)
            assert prod1.current_stock == 97, f"Stock expected 97, got {prod1.current_stock}"
            assert cust1.current_balance == 35, f"Due expected 35, got {cust1.current_balance}"
            
            call_edit_sale_post(s_id, cust1.id, 10, 0, [prod1.id], [1], [15]) # decrease qty to 1, total 15, paid 10, due 5
            db.session.refresh(prod1)
            db.session.refresh(cust1)
            assert prod1.current_stock == 99, f"Stock expected 99, got {prod1.current_stock}"
            assert cust1.current_balance == 5, f"Due expected 5, got {cust1.current_balance}"
            
            # Scenario 3: Change product
            print("Running Scenario 3: Change Product...")
            call_edit_sale_post(s_id, cust1.id, 10, 0, [prod2.id], [1], [30]) # total 30, paid 10, due 20
            db.session.refresh(prod1)
            db.session.refresh(prod2)
            db.session.refresh(cust1)
            assert prod1.current_stock == 100
            assert prod2.current_stock == 99
            assert cust1.current_balance == 20
            
            # Scenario 4: Change customer
            print("Running Scenario 4: Change Customer...")
            call_edit_sale_post(s_id, cust2.id, 10, 0, [prod2.id], [1], [30])
            db.session.refresh(cust1)
            db.session.refresh(cust2)
            assert cust1.current_balance == 0 # Reverted
            assert cust2.current_balance == -30 # original -50, now +20 due = -30
            
            # Scenario 5 & 6: Change paid amount & discount
            print("Running Scenarios 5 & 6: Change Paid Amount & Discount...")
            call_edit_sale_post(s_id, cust2.id, 15, 5, [prod2.id], [1], [30]) # total=25, paid=15, due=10
            db.session.refresh(cust2)
            assert cust2.current_balance == -40 # -50 + 10 = -40
            
            db.session.expire_all()
            sale = Sale.query.get(s_id)
            all_clgs = CashLedger.query.filter_by(voucher_no=sale.invoice_no).all()
            for c in all_clgs:
                print(f"CASH LEDGER DB: id={c.id}, amount={c.amount}")
            cash_lg = CashLedger.query.filter_by(voucher_no=sale.invoice_no).order_by(CashLedger.id.desc()).first()
            assert cash_lg.amount == 15, f"Expected 15, got {cash_lg.amount}"
            assert cash_lg.running_balance == baseline_cash_running + 15
            
            # Scenario 7 & 8: Add/Remove product lines
            print("Running Scenarios 7 & 8: Add/Remove Product Lines...")
            call_edit_sale_post(s_id, cust2.id, 15, 5, [prod2.id, prod1.id], [1, 2], [30, 15])
            # Total = (30 + 30) - 5 = 55. Paid 15. Due 40.
            db.session.refresh(cust2)
            assert cust2.current_balance == -10
            db.session.refresh(prod1)
            assert prod1.current_stock == 98
            
            call_edit_sale_post(s_id, cust2.id, 15, 5, [prod1.id], [2], [15]) # Total=30 - 5 = 25. Paid 15, Due 10.
            db.session.refresh(cust2)
            db.session.refresh(prod2)
            assert cust2.current_balance == -40
            assert prod2.current_stock == 100
            
            # Scenario 10: Insufficient stock (Should fail and rollback)
            print("Running Scenario 10: Insufficient Stock...")
            call_edit_sale_post(s_id, cust2.id, 15, 5, [prod1.id], [105], [15]) # stock only 100, currently 98. 98+2=100. 100-105 = -5 (Fail)
            db.session.refresh(prod1)
            db.session.refresh(cust2)
            assert prod1.current_stock == 98 # Rolled back!
            assert cust2.current_balance == -40
            
            # Cleanup
            print("Cleaning up...")
            db.session.delete(Sale.query.get(s_id))
            db.session.delete(cust1)
            db.session.delete(cust2)
            db.session.delete(prod1)
            db.session.delete(prod2)
            db.session.commit()
            print("Sale Edit Feature Fully Verified")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print("TEST FAILED")
            db.session.rollback()

if __name__ == '__main__':
    run_tests()
