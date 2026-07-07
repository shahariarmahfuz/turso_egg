from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from models import db, ExpenseEntry, CashOut, Purchase, PurchaseReturn, Sale, SaleItem, dhaka_now_date

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def index():
    return redirect(url_for('routes.dashboard'))

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    today = dhaka_now_date()
    
    total_expense = db.session.query(db.func.sum(ExpenseEntry.amount)).filter(ExpenseEntry.date == today).scalar() or 0.00
    total_cash_out = db.session.query(db.func.sum(CashOut.amount)).filter(CashOut.date == today).scalar() or 0.00
    
    cash_purchase_base = db.session.query(db.func.sum(Purchase.cash_paid)).filter(Purchase.purchase_date == today).scalar() or 0.00
    purchase_due_base = db.session.query(db.func.sum(Purchase.due_amount)).filter(Purchase.purchase_date == today).scalar() or 0.00

    cash_refund = db.session.query(db.func.sum(PurchaseReturn.cash_refund)).filter(PurchaseReturn.return_date == today).scalar() or 0.00
    due_adjustment = db.session.query(db.func.sum(PurchaseReturn.due_adjustment)).filter(PurchaseReturn.return_date == today).scalar() or 0.00
    
    cash_purchase = cash_purchase_base - cash_refund
    purchase_due = purchase_due_base - due_adjustment
    
    cash_sale = db.session.query(db.func.sum(Sale.cash_paid)).filter(Sale.sale_date == today).scalar() or 0.00
    sale_due = db.session.query(db.func.sum(Sale.due_amount)).filter(Sale.sale_date == today).scalar() or 0.00
    sale_income = db.session.query(db.func.sum(SaleItem.profit)).join(Sale).filter(Sale.sale_date == today).scalar() or 0.00

    summary_data = {
        'cash_sale': cash_sale,
        'cash_purchase': cash_purchase,
        'sale_due': sale_due,
        'purchase_due': purchase_due,
        'sale_return': 0.00,
        'sale_income': sale_income,
        'return_due': 0.00,
        'expense': total_expense,
        'cash_out': total_cash_out
    }
    return render_template('dashboard.html', data=summary_data, dashboard_title="Dashboard", dashboard_subtitle="Today's Business Summary")

@routes_bp.route('/all_time_dashboard')
@login_required
def all_time_dashboard():
    from flask import g
    effective_baseline = None
    if g.business and getattr(g.business, 'dashboard_baseline_date', None):
        business_creation_date = g.business.created_at.date() if g.business.created_at else None
        if business_creation_date:
            effective_baseline = max(business_creation_date, g.business.dashboard_baseline_date)
        else:
            effective_baseline = g.business.dashboard_baseline_date

    q_expense = db.session.query(db.func.sum(ExpenseEntry.amount))
    q_cash_out = db.session.query(db.func.sum(CashOut.amount))
    q_pur_cash = db.session.query(db.func.sum(Purchase.cash_paid))
    q_pur_due = db.session.query(db.func.sum(Purchase.due_amount))
    q_pur_ret_cash = db.session.query(db.func.sum(PurchaseReturn.cash_refund))
    q_pur_ret_due = db.session.query(db.func.sum(PurchaseReturn.due_adjustment))
    q_sale_cash = db.session.query(db.func.sum(Sale.cash_paid))
    q_sale_due = db.session.query(db.func.sum(Sale.due_amount))
    q_sale_inc = db.session.query(db.func.sum(SaleItem.profit)).join(Sale)

    if effective_baseline:
        q_expense = q_expense.filter(ExpenseEntry.date >= effective_baseline)
        q_cash_out = q_cash_out.filter(CashOut.date >= effective_baseline)
        q_pur_cash = q_pur_cash.filter(Purchase.purchase_date >= effective_baseline)
        q_pur_due = q_pur_due.filter(Purchase.purchase_date >= effective_baseline)
        q_pur_ret_cash = q_pur_ret_cash.filter(PurchaseReturn.return_date >= effective_baseline)
        q_pur_ret_due = q_pur_ret_due.filter(PurchaseReturn.return_date >= effective_baseline)
        q_sale_cash = q_sale_cash.filter(Sale.sale_date >= effective_baseline)
        q_sale_due = q_sale_due.filter(Sale.sale_date >= effective_baseline)
        q_sale_inc = q_sale_inc.filter(Sale.sale_date >= effective_baseline)

    total_expense = q_expense.scalar() or 0.00
    total_cash_out = q_cash_out.scalar() or 0.00
    cash_purchase_base = q_pur_cash.scalar() or 0.00
    purchase_due_base = q_pur_due.scalar() or 0.00
    cash_refund = q_pur_ret_cash.scalar() or 0.00
    due_adjustment = q_pur_ret_due.scalar() or 0.00
    
    cash_purchase = cash_purchase_base - cash_refund
    purchase_due = purchase_due_base - due_adjustment
    
    cash_sale = q_sale_cash.scalar() or 0.00
    sale_due = q_sale_due.scalar() or 0.00
    sale_income = q_sale_inc.scalar() or 0.00

    summary_data = {
        'cash_sale': cash_sale,
        'cash_purchase': cash_purchase,
        'sale_due': sale_due,
        'purchase_due': purchase_due,
        'sale_return': 0.00,
        'sale_income': sale_income,
        'return_due': 0.00,
        'expense': total_expense,
        'cash_out': total_cash_out
    }
    return render_template('dashboard.html', data=summary_data, dashboard_title="All-Time Dashboard", dashboard_subtitle="Cumulative Business Summary")
