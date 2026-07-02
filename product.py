from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from auth import admin_required
from models import db, Product
import random
import string

product_bp = Blueprint('product', __name__, url_prefix='/product')

def generate_product_code():
    return 'PRD-' + ''.join(random.choices(string.digits, k=4))

@product_bp.route('/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        category = request.form.get('category')
        brand = request.form.get('brand')
        unit = request.form.get('unit')
        
        try:
            cost_price = float(request.form.get('cost_price', 0))
            selling_price = float(request.form.get('selling_price', 0))
            opening_stock = float(request.form.get('opening_stock', 0))
            min_stock_alert = float(request.form.get('min_stock_alert', 0))
        except ValueError:
            flash("Numeric fields must be valid numbers.", "danger")
            return redirect(url_for('product.add_product'))
        
        barcode = request.form.get('barcode')
        description = request.form.get('description')
        status = request.form.get('status', 'Active')
        
        # generate product code
        product_code = generate_product_code()
        while Product.query.filter_by(product_code=product_code).first():
            product_code = generate_product_code()
            
        new_product = Product(
            product_code=product_code,
            product_name=product_name,
            category=category,
            brand=brand,
            unit=unit,
            cost_price=cost_price,
            selling_price=selling_price,
            opening_stock=opening_stock,
            current_stock=opening_stock, # Opening stock initializes current stock
            min_stock_alert=min_stock_alert,
            barcode=barcode,
            description=description,
            status=status
        )
        
        try:
            db.session.add(new_product)
            db.session.commit()
            flash("Product added successfully!", "success")
            return redirect(url_for('product.add_product'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding product: {str(e)}", "danger")
            
    return render_template('add_product.html')

@product_bp.route('/manage_product')
@login_required
@admin_required
def manage_product():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('manage_product.html', products=products)

@product_bp.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.product_name = request.form.get('product_name')
        product.category = request.form.get('category')
        product.brand = request.form.get('brand')
        product.unit = request.form.get('unit')
        try:
            product.cost_price = float(request.form.get('cost_price', product.cost_price))
            product.selling_price = float(request.form.get('selling_price', product.selling_price))
            product.min_stock_alert = float(request.form.get('min_stock_alert', product.min_stock_alert))
            
            # Note: usually we don't allow changing opening stock as it messes up accounting, 
            # but if required we can update current stock based on difference. 
            # For this simple app, we might just allow editing fields directly.
        except ValueError:
            flash("Numeric fields must be valid numbers.", "danger")
            return redirect(url_for('product.edit_product', id=product.id))
        
        product.barcode = request.form.get('barcode')
        product.description = request.form.get('description')
        product.status = request.form.get('status', product.status)
        
        try:
            db.session.commit()
            flash("Product updated successfully!", "success")
            return redirect(url_for('product.manage_product'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating product: {str(e)}", "danger")
            
    return render_template('edit_product.html', product=product)

@product_bp.route('/delete_product/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Cannot delete this product because it is referenced in other records.", "danger")
    return redirect(url_for('product.manage_product'))

@product_bp.route('/product-list', methods=['GET'])
@login_required
def product_list():
    return render_template('product_list.html')

@product_bp.route('/api/list', methods=['GET'])
@login_required
def api_product_list():
    products = Product.query.order_by(Product.id.desc()).all()
    is_admin = current_user.role == 'Admin'
    data = []
    for p in products:
        stock_status = "Out of Stock"
        if p.current_stock > (p.min_stock_alert or 0):
            stock_status = "In Stock"
        elif p.current_stock > 0:
            stock_status = "Low Stock"
            
        data.append({
            'product_code': p.product_code,
            'product_name': p.product_name,
            'category': p.category or '',
            'brand': p.brand or '',
            'unit': p.unit or '',
            'cost_price': float(p.cost_price) if is_admin and p.cost_price else 0.0,
            'selling_price': float(p.selling_price) if p.selling_price else 0.0,
            'current_stock': float(p.current_stock) if p.current_stock else 0.0,
            'stock_status': stock_status
        })
    return jsonify({'data': data})
