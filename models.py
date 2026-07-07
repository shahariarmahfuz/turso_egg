from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from zoneinfo import ZoneInfo
import random
import string

def dhaka_now():
    return datetime.now(ZoneInfo("Asia/Dhaka")).replace(tzinfo=None)

def dhaka_now_date():
    return dhaka_now().date()

db = SQLAlchemy()


class Business(db.Model):
    __tablename__ = 'businesses'
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(150), nullable=False)
    business_slug = db.Column(db.String(150), unique=True, nullable=False)
    status = db.Column(db.String(50), default='Active')
    created_at = db.Column(db.DateTime, default=dhaka_now)
    dashboard_baseline_date = db.Column(db.Date, nullable=True)

def generate_avatar_seed():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    name = db.Column(db.String(150), nullable=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Employee')
    status = db.Column(db.String(50), nullable=False, default='Active')
    is_hidden = db.Column(db.Boolean, default=False, server_default='0')
    avatar_seed = db.Column(db.String(50), nullable=True, default=generate_avatar_seed)
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=dhaka_now)
    updated_at = db.Column(db.DateTime, default=dhaka_now, onupdate=dhaka_now)

def generate_head_code():
    return 'EH-' + ''.join(random.choices(string.digits, k=4))

def generate_invoice_no():
    return 'INV-' + ''.join(random.choices(string.digits, k=6))

class ExpenseHead(db.Model):
    __tablename__ = 'expense_heads'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    head_name = db.Column(db.String(100), unique=True, nullable=False)
    head_code = db.Column(db.String(50), unique=True, nullable=False, default=generate_head_code)
    created_date = db.Column(db.Date, default=dhaka_now_date)
    entries = db.relationship('ExpenseEntry', backref='expense_head', lazy=True, cascade="all, delete-orphan")

class ExpenseEntry(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False, default=generate_invoice_no)
    expense_head_id = db.Column(db.Integer, db.ForeignKey('expense_heads.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    comment = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=dhaka_now)

class CashOut(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    type = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=dhaka_now)
    updated_at = db.Column(db.DateTime, default=dhaka_now, onupdate=dhaka_now)

def generate_supplier_code():
    return 'SUP-' + ''.join(random.choices(string.digits, k=4))

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    __table_args__ = (
        db.UniqueConstraint('business_id', 'supplier_name', name='uq_business_supplier_name'),
    )
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    supplier_code = db.Column(db.String(50), unique=True, nullable=False, default=generate_supplier_code)
    supplier_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    previous_balance = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0)
    created_date = db.Column(db.Date, default=dhaka_now_date)
    created_at = db.Column(db.DateTime, default=dhaka_now)
    updated_at = db.Column(db.DateTime, default=dhaka_now, onupdate=dhaka_now)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    product_code = db.Column(db.String(50), unique=True, nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    unit = db.Column(db.String(20), default='Pcs')
    cost_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    opening_stock = db.Column(db.Float, default=0.0)
    current_stock = db.Column(db.Float, default=0.0)
    min_stock_alert = db.Column(db.Float, default=0.0)
    barcode = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Active')

def generate_purchase_invoice():
    return 'PUR-' + ''.join(random.choices(string.digits, k=6))

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False, default=generate_purchase_invoice)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    bill_number = db.Column(db.String(50), nullable=True)
    transport_cost = db.Column(db.Float, default=0.0)
    other_cost = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    cash_paid = db.Column(db.Float, default=0.0)
    due_amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(20), default='Cash')
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=dhaka_now)
    
    supplier = db.relationship('Supplier', backref='purchases', lazy=True)

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    purchase = db.relationship('Purchase', backref=db.backref('items', cascade="all, delete-orphan"), lazy=True)
    product = db.relationship('Product', backref='purchase_items', lazy=True)

def generate_return_invoice():
    return 'PR-' + ''.join(random.choices(string.digits, k=6))

class PurchaseReturn(db.Model):
    __tablename__ = 'purchase_returns'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    return_invoice = db.Column(db.String(50), unique=True, nullable=False, default=generate_return_invoice)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    transport_cost = db.Column(db.Float, default=0.0)
    other_cost = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    cash_refund = db.Column(db.Float, default=0.0)
    due_adjustment = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(20), default='Cash')
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=dhaka_now)
    
    supplier = db.relationship('Supplier', backref='purchase_returns', lazy=True)
    purchase = db.relationship('Purchase', backref='purchase_returns', lazy=True)

class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_items'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    return_id = db.Column(db.Integer, db.ForeignKey('purchase_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    purchase_return = db.relationship('PurchaseReturn', backref=db.backref('items', cascade="all, delete-orphan"), lazy=True)
    product = db.relationship('Product', backref='return_items', lazy=True)

def generate_customer_code():
    return 'CUST-' + ''.join(random.choices(string.digits, k=4))

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    customer_code = db.Column(db.String(50), unique=True, nullable=False, default=generate_customer_code)
    customer_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    previous_balance = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0)
    created_date = db.Column(db.Date, default=dhaka_now_date)
    created_at = db.Column(db.DateTime, default=dhaka_now)
    updated_at = db.Column(db.DateTime, default=dhaka_now, onupdate=dhaka_now)

def generate_sale_invoice():
    return 'INV-' + ''.join(random.choices(string.digits, k=6))

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False, default=generate_sale_invoice)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    sale_date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    bill_number = db.Column(db.String(50), nullable=True)
    transport_cost = db.Column(db.Float, default=0.0)
    labour_cost = db.Column(db.Float, default=0.0)
    vat = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    cash_paid = db.Column(db.Float, default=0.0)
    due_amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(20), default='Cash')
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=dhaka_now)
    
    customer = db.relationship('Customer', backref='sales', lazy=True)

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    sale = db.relationship('Sale', backref=db.backref('items', cascade="all, delete-orphan"), lazy=True)
    product = db.relationship('Product', backref='sale_items', lazy=True)

class CustomerLedger(db.Model):
    __tablename__ = 'customer_ledgers'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    invoice_no = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    debit = db.Column(db.Float, default=0.0)
    credit = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=dhaka_now)

    customer = db.relationship('Customer', backref=db.backref('ledger_entries', cascade="all, delete-orphan"), lazy=True)

def generate_sale_return_invoice():
    return 'SR-' + ''.join(random.choices(string.digits, k=6))

class SaleReturn(db.Model):
    __tablename__ = 'sale_returns'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    return_invoice = db.Column(db.String(50), unique=True, nullable=False, default=generate_sale_return_invoice)
    sale_invoice = db.Column(db.String(50), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    subtotal = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    paid = db.Column(db.Float, default=0.0)
    due = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(50), default='Cash')
    note = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=dhaka_now)

    customer = db.relationship('Customer', backref='sale_returns', lazy=True)
    admin = db.relationship('Admin', backref='sale_returns', lazy=True)

class SaleReturnItem(db.Model):
    __tablename__ = 'sale_return_items'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    return_id = db.Column(db.Integer, db.ForeignKey('sale_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

    sale_return = db.relationship('SaleReturn', backref=db.backref('items', cascade="all, delete-orphan"), lazy=True)
    product = db.relationship('Product', backref='sale_return_items', lazy=True)

def generate_collection_voucher():
    return 'COL-' + ''.join(random.choices(string.digits, k=6))

class CustomerCollection(db.Model):
    __tablename__ = 'customer_collections'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    voucher_no = db.Column(db.String(50), unique=True, nullable=False, default=generate_collection_voucher)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    previous_due = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    cash_paid = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(50), default='Cash')
    bank_name = db.Column(db.String(100), nullable=True)
    cheque_number = db.Column(db.String(100), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=dhaka_now)

    customer = db.relationship('Customer', backref=db.backref('collections', cascade="all, delete-orphan"), lazy=True)
    admin = db.relationship('Admin', backref='collections', lazy=True)

class CashLedger(db.Model):
    __tablename__ = 'cash_ledgers'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    voucher_no = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Float, default=0.0)
    type = db.Column(db.String(20), nullable=False) # 'In' or 'Out'
    date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    running_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=dhaka_now)

class Bank(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    bank_name = db.Column(db.String(150), nullable=False)
    account_name = db.Column(db.String(150), nullable=False)
    account_number = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=True)
    current_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=dhaka_now)

class BankTransaction(db.Model):
    __tablename__ = 'bank_transactions'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    description = db.Column(db.String(255), nullable=True)
    code = db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    cheque_number = db.Column(db.String(100), nullable=True)
    credit = db.Column(db.Float, default=0.0) # Deposit
    debit = db.Column(db.Float, default=0.0) # Withdrawal
    running_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=dhaka_now)

    bank = db.relationship('Bank', backref=db.backref('transactions', cascade="all, delete-orphan"), lazy=True)


def generate_supplier_payment_voucher():
    import random, string
    return 'SP-' + ''.join(random.choices(string.digits, k=6))

class SupplierPayment(db.Model):
    __tablename__ = 'supplier_payments'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    voucher_no = db.Column(db.String(50), unique=True, nullable=False, default=generate_supplier_payment_voucher)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=dhaka_now_date)
    previous_due = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    cash_paid = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(50), default='Cash')
    bank_name = db.Column(db.String(100), nullable=True)
    cheque_number = db.Column(db.String(100), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=dhaka_now)

    supplier = db.relationship('Supplier', backref=db.backref('payments', cascade="all, delete-orphan"), lazy=True)
    admin = db.relationship('Admin', backref='supplier_payments', lazy=True)

class SupplierLedger(db.Model):
    __tablename__ = 'supplier_ledgers'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    invoice_no = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    debit = db.Column(db.Float, default=0.0)
    credit = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=dhaka_now)

    supplier = db.relationship('Supplier', backref=db.backref('ledger_entries', cascade="all, delete-orphan"), lazy=True)


from sqlalchemy import event
from sqlalchemy.orm import Query
from flask import g, has_request_context

@event.listens_for(Query, "before_compile", retval=True)
def before_compile(query):
    if has_request_context() and getattr(g, 'business', None):
        for column_description in query.column_descriptions:
            entity = column_description['entity']
            if entity is None:
                continue
            if hasattr(entity, 'business_id') and getattr(entity, '__name__', '') != 'Business':
                query = query.enable_assertions(False).filter(entity.business_id == g.business.id)
    return query

@event.listens_for(db.Model, 'before_insert', propagate=True)
def receive_before_insert(mapper, connection, target):
    if hasattr(target, 'business_id') and getattr(target, '__class__', None) and target.__class__.__name__ != 'Business':
        if not target.business_id and has_request_context() and getattr(g, 'business', None):
            target.business_id = g.business.id
