from flask import Blueprint, render_template, request
from flask_login import login_required
from auth import admin_required
from models import db, ExpenseEntry, ExpenseHead, Sale, SaleReturn, Purchase, PurchaseItem, CashLedger, Bank, BankTransaction
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
    total = sum(e.amount for e in expenses)
    
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
    total_sales_amount = sum(s.subtotal for s in sales)
    sales_discount = sum(s.discount for s in sales)
    
    # Calculate COGS from SaleItems
    cogs = 0
    for s in sales:
        for i in s.items:
            cogs += (i.cost_price * i.quantity)
            
    # Calculate Returns
    returns = s_ret_q.all()
    total_returns = sum(r.subtotal for r in returns)
    
    net_sales = total_sales_amount - total_returns - sales_discount
    gross_profit = net_sales - cogs
    
    expenses = exp_q.all()
    office_expense = sum(e.amount for e in expenses)
    
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
@admin_required
def bank_report():
    # Fetch all banks
    banks = Bank.query.order_by(Bank.bank_name).all()
    return render_template('bank_report.html', banks=banks)

@account_reports_bp.route('/bank_statement')
@login_required
@admin_required
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

@account_reports_bp.route('/cash_book')
@login_required
@admin_required
def cash_book():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    q = CashLedger.query
    
    previous_balance = 0
    if from_date:
        fd = datetime.strptime(from_date, '%Y-%m-%d').date()
        prev = CashLedger.query.filter(CashLedger.date < fd).all()
        for p in prev:
            if p.type == 'In': previous_balance += p.amount
            if p.type == 'Out': previous_balance -= p.amount
        q = q.filter(CashLedger.date >= fd)
        
    if to_date:
        td = datetime.strptime(to_date, '%Y-%m-%d').date()
        q = q.filter(CashLedger.date <= td)
        
    ledgers = q.order_by(CashLedger.date, CashLedger.id).all()
    
    today_receive = 0
    today_expense = 0
    
    running = previous_balance
    for lg in ledgers:
        if lg.type == 'In':
            running += lg.amount
            today_receive += lg.amount
        else:
            running -= lg.amount
            today_expense += lg.amount
        lg.display_balance = running
        
    cash_in_hand = running
        
    return render_template('cash_book.html', ledgers=ledgers, from_date=from_date, to_date=to_date,
                           previous_balance=previous_balance, today_receive=today_receive,
                           today_expense=today_expense, cash_in_hand=cash_in_hand)
