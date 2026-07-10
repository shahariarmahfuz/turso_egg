from flask import Blueprint, render_template, request
from flask_login import login_required
from auth import admin_required
from models import db, ExpenseEntry, ExpenseHead, Sale, SaleItem, SaleReturn, Purchase, PurchaseItem, CashLedger, Bank, BankTransaction, CustomerCollection, SupplierPayment
from datetime import datetime
from sqlalchemy import func

account_reports_bp = Blueprint('account_reports', __name__, url_prefix='/account_reports')

@account_reports_bp.route('/expense_report')
@login_required
def expense_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    head_id = request.args.get('head_id')
    
    query = ExpenseEntry.query
    if from_date:
        query = query.filter(ExpenseEntry.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(ExpenseEntry.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    if head_id:
        query = query.filter(ExpenseEntry.head_id == head_id)
        
    expenses = query.order_by(ExpenseEntry.date.desc()).all()
    heads = ExpenseHead.query.order_by(ExpenseHead.head_name).all()
    total = query.with_entities(db.func.sum(ExpenseEntry.amount)).scalar() or 0.0
    
    return render_template('expense_report.html', expenses=expenses, heads=heads, total=total,
                           from_date=from_date, to_date=to_date, head_id=head_id)

@account_reports_bp.route('/income_report')
@login_required
def income_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    sale_q = Sale.query
    s_ret_q = SaleReturn.query
    exp_q = ExpenseEntry.query
    
    if from_date:
        from_d = datetime.strptime(from_date, '%Y-%m-%d').date()
        sale_q = sale_q.filter(Sale.sale_date >= from_d)
        s_ret_q = s_ret_q.filter(SaleReturn.date >= from_d)
        exp_q = exp_q.filter(ExpenseEntry.date >= from_d)
    if to_date:
        to_d = datetime.strptime(to_date, '%Y-%m-%d').date()
        sale_q = sale_q.filter(Sale.sale_date <= to_d)
        s_ret_q = s_ret_q.filter(SaleReturn.date <= to_d)
        exp_q = exp_q.filter(ExpenseEntry.date <= to_d)
        
    sales = sale_q.all()
    total_sales_amount = sale_q.with_entities(db.func.sum(Sale.subtotal)).scalar() or 0.0
    sales_discount = sale_q.with_entities(db.func.sum(Sale.discount)).scalar() or 0.0
    
    # Calculate COGS from SaleItems
    cogs = sale_q.join(SaleItem).with_entities(db.func.sum(SaleItem.cost_price * SaleItem.quantity)).scalar() or 0.0
            
    # Calculate Returns
    returns = s_ret_q.all()
    total_returns = s_ret_q.with_entities(db.func.sum(SaleReturn.subtotal)).scalar() or 0.0
    
    net_sales = total_sales_amount - total_returns - sales_discount
    gross_profit = net_sales - cogs
    
    expenses = exp_q.all()
    office_expense = exp_q.with_entities(db.func.sum(ExpenseEntry.amount)).scalar() or 0.0
    
    net_profit = gross_profit - office_expense
    
    return render_template('income_report.html', 
                           from_date=from_date, to_date=to_date,
                           total_sales_amount=total_sales_amount,
                           sales_discount=sales_discount,
                           total_returns=total_returns,
                           net_sales=net_sales,
                           cogs=cogs,
                           gross_profit=gross_profit,
                           office_expense=office_expense,
                           net_profit=net_profit)

@account_reports_bp.route('/bank_report')
@login_required
def bank_report():
    # Fetch all banks
    banks = Bank.query.order_by(Bank.bank_name).all()
    return render_template('bank_report.html', banks=banks)

@account_reports_bp.route('/bank_statement')
@login_required
def bank_statement():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    bank_id = request.args.get('bank_id')
    
    transactions = []
    opening_balance = 0
    total_credit = 0
    total_debit = 0
    closing_balance = 0
    
    if bank_id:
        q = BankTransaction.query.filter_by(bank_id=bank_id)
        
        # Calculate opening balance
        if from_date:
            fd = datetime.strptime(from_date, '%Y-%m-%d').date()
            prev_txs = BankTransaction.query.filter_by(bank_id=bank_id).filter(BankTransaction.date < fd).all()
            opening_balance = sum(t.credit for t in prev_txs) - sum(t.debit for t in prev_txs)
            q = q.filter(BankTransaction.date >= fd)
            
        if to_date:
            td = datetime.strptime(to_date, '%Y-%m-%d').date()
            q = q.filter(BankTransaction.date <= td)
            
        transactions = q.order_by(BankTransaction.date, BankTransaction.id).all()
        
        running = opening_balance
        for tx in transactions:
            running += tx.credit - tx.debit
            tx.display_balance = running
            total_credit += tx.credit
            total_debit += tx.debit
            
        closing_balance = opening_balance + total_credit - total_debit

    banks = Bank.query.order_by(Bank.bank_name).all()
    return render_template('bank_statement.html', banks=banks, transactions=transactions,
                           opening_balance=opening_balance, total_credit=total_credit,
                           total_debit=total_debit, closing_balance=closing_balance,
                           from_date=from_date, to_date=to_date, bank_id=bank_id)

class CashEntry:
    def __init__(self, date, type, voucher_no, description, display_name, amount, source):
        self.date = date
        self.type = type
        self.voucher_no = voucher_no
        self.description = description
        self.display_name = display_name
        self.amount = amount
        self.source = source
        self.display_balance = 0.0

def get_cash_book_data(from_date, to_date):
    from models import CashOut
    entries = []
    
    # 1. Sales
    sales = Sale.query.filter(Sale.cash_paid > 0).all()
    for s in sales:
        entries.append(CashEntry(s.sale_date, 'In', s.invoice_no, "Sale Product in Cash", s.customer.customer_name if s.customer else "Cash Customer", s.cash_paid, 'Cash Sales'))

    # 2. Customer Collections
    cols = CustomerCollection.query.filter(CustomerCollection.cash_paid > 0).all()
    for c in cols:
        entries.append(CashEntry(c.date, 'In', c.voucher_no, "Customer Collection", c.customer.customer_name if c.customer else "", c.cash_paid, 'Customer Collections'))
        
    # 3. Expenses
    exps = ExpenseEntry.query.all()
    for e in exps:
        entries.append(CashEntry(e.date, 'Out', e.invoice_no, e.comment or f"Expense: {e.expense_head.head_name}", "", e.amount, 'Expenses'))
        
    # 4. Cash Out
    couts = CashOut.query.all()
    for c in couts:
        if c.type == 'Cash In':
            entries.append(CashEntry(c.date, 'In', '', c.comment or "Other Cash Income", "", c.amount, 'Other Cash Income'))
        else:
            entries.append(CashEntry(c.date, 'Out', '', c.comment or "Cash Out", "", c.amount, 'Cash Out'))
        
    # 5. Purchases
    purs = Purchase.query.filter(Purchase.cash_paid > 0).all()
    for p in purs:
        entries.append(CashEntry(p.purchase_date, 'Out', p.invoice_no, "Cash Purchase", p.supplier.supplier_name if p.supplier else "", p.cash_paid, 'Cash Purchases'))
        
    # 6. Supplier Payments
    spays = SupplierPayment.query.filter(SupplierPayment.cash_paid > 0).all()
    for sp in spays:
        entries.append(CashEntry(sp.date, 'Out', sp.voucher_no, "Supplier Payment", sp.supplier.supplier_name if sp.supplier else "", sp.cash_paid, 'Supplier Payments'))

    # Sort entries by date
    entries.sort(key=lambda x: x.date)

    fd = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
    td = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
    
    summary = {
        'cash_sales': 0.0,
        'customer_collections': 0.0,
        'other_income': 0.0,
        'expenses': 0.0,
        'cash_out': 0.0,
        'cash_purchases': 0.0,
        'supplier_payments': 0.0,
    }
    
    running = 0.0
    period_entries = []
    
    for e in entries:
        is_before = False
        if fd and e.date < fd:
            is_before = True
            
        is_after = False
        if td and e.date > td:
            is_after = True
            
        if is_before:
            if e.type == 'In':
                running += e.amount
            else:
                running -= e.amount
        elif not is_after:
            if e.type == 'In':
                running += e.amount
                if e.source == 'Cash Sales': summary['cash_sales'] += e.amount
                elif e.source == 'Customer Collections': summary['customer_collections'] += e.amount
                else: summary['other_income'] += e.amount
            else:
                running -= e.amount
                if e.source == 'Expenses': summary['expenses'] += e.amount
                elif e.source == 'Cash Out': summary['cash_out'] += e.amount
                elif e.source == 'Cash Purchases': summary['cash_purchases'] += e.amount
                elif e.source == 'Supplier Payments': summary['supplier_payments'] += e.amount
            
            e.display_balance = running
            period_entries.append(e)

    opening_balance = period_entries[0].display_balance - (period_entries[0].amount if period_entries[0].type == 'In' else -period_entries[0].amount) if period_entries else running
    if not period_entries and fd:
        opening_balance = running
        
    summary['opening_balance'] = opening_balance
    summary['total_in'] = summary['cash_sales'] + summary['customer_collections'] + summary['other_income']
    summary['total_out'] = summary['expenses'] + summary['cash_out'] + summary['cash_purchases'] + summary['supplier_payments']
    summary['closing_balance'] = running
    
    return period_entries, summary

@account_reports_bp.route('/cash_book')
@login_required
def cash_book():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    ledgers, summary = get_cash_book_data(from_date, to_date)
    return render_template('cash_book.html', ledgers=ledgers, summary=summary, from_date=from_date, to_date=to_date)

@account_reports_bp.route('/cash_book_print')
@login_required
def cash_book_print():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    ledgers, summary = get_cash_book_data(from_date, to_date)
    return render_template('cash_book_print.html', ledgers=ledgers, summary=summary, from_date=from_date, to_date=to_date)
