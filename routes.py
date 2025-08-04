from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, date
from app import app, db
from models import User, Product, Inventory, Order, OrderItem, Category, Role, StaffSchedule, AIInsight, OrderStatus, OrderType
from forms import LoginForm, UserForm, ProductForm, InventoryForm, OrderForm, CategoryForm
from utils import generate_order_number, generate_ai_insights, requires_role
import logging


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.is_active:
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard')
                return redirect(next_page)
            else:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics
    stats = {}
    
    if current_user.role.name in ['admin', 'manager']:
        stats['total_orders'] = Order.query.count()
        stats['pending_orders'] = Order.query.filter_by(status=OrderStatus.PENDING).count()
        stats['total_customers'] = User.query.join(Role).filter(Role.name == 'customer').count()
        stats['low_stock_items'] = len([inv for inv in Inventory.query.all() if inv.is_low_stock()])
        stats['total_revenue'] = sum([o.total_amount for o in Order.query.filter(Order.status != OrderStatus.CANCELLED).all()])
        
        # Recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        # AI Insights
        ai_insights = AIInsight.query.filter_by(is_active=True).order_by(AIInsight.created_at.desc()).limit(3).all()
        
        return render_template('dashboard.html', stats=stats, recent_orders=recent_orders, ai_insights=ai_insights)
    
    elif current_user.role.name == 'staff':
        # Staff dashboard - show their schedule and current orders
        today = date.today()
        schedule = StaffSchedule.query.filter_by(staff_id=current_user.id, date=today).first()
        active_orders = Order.query.filter(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION])).limit(10).all()
        
        return render_template('dashboard.html', schedule=schedule, active_orders=active_orders)
    
    else:  # customer
        # Customer dashboard - show their orders
        customer_orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).limit(10).all()
        return render_template('dashboard.html', customer_orders=customer_orders)


@app.route('/inventory')
@login_required
@requires_role(['admin', 'manager', 'staff'])
def inventory():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = db.session.query(Inventory).join(Product)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    inventory_items = query.paginate(page=page, per_page=20, error_out=False)
    low_stock_items = [inv for inv in Inventory.query.all() if inv.is_low_stock()]
    
    return render_template('inventory.html', inventory_items=inventory_items, 
                         low_stock_items=low_stock_items, search=search)


@app.route('/inventory/update/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def update_inventory(id):
    inventory_item = Inventory.query.get_or_404(id)
    form = InventoryForm(obj=inventory_item)
    
    if form.validate_on_submit():
        form.populate_obj(inventory_item)
        inventory_item.last_updated = datetime.utcnow()
        db.session.commit()
        flash('Inventory updated successfully!', 'success')
        return redirect(url_for('inventory'))
    
    return render_template('inventory.html', form=form, inventory_item=inventory_item)


@app.route('/products')
@login_required
@requires_role(['admin', 'manager'])
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.paginate(page=page, per_page=20, error_out=False)
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('products.html', products=products, categories=categories, search=search)


@app.route('/products/new', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def new_product():
    form = ProductForm()
    
    if form.validate_on_submit():
        product = Product()
        form.populate_obj(product)
        db.session.add(product)
        db.session.flush()  # Get the product ID
        
        # Create inventory entry
        inventory = Inventory(product_id=product.id, quantity=0)
        db.session.add(inventory)
        db.session.commit()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('product_form.html', form=form, title='New Product')


@app.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    order_type_filter = request.args.get('type', '')
    
    query = Order.query
    
    if current_user.role.name == 'customer':
        query = query.filter_by(customer_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=OrderStatus(status_filter))
    
    if order_type_filter:
        query = query.filter_by(order_type=OrderType(order_type_filter))
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('orders.html', orders=orders, status_filter=status_filter, 
                         order_type_filter=order_type_filter)


@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager', 'staff'])
def new_order():
    form = OrderForm()
    
    # Populate customer choices
    customers = User.query.join(Role).filter(Role.name == 'customer').all()
    form.customer_id.choices = [(c.id, f"{c.first_name} {c.last_name}") for c in customers]
    
    if form.validate_on_submit():
        order = Order(
            order_number=generate_order_number(),
            total_amount=0  # Will be calculated when items are added
        )
        form.populate_obj(order)
        db.session.add(order)
        db.session.commit()
        
        flash('Order created successfully!', 'success')
        return redirect(url_for('orders'))
    
    return render_template('order_form.html', form=form, title='New Order')


@app.route('/catering')
@login_required
def catering():
    page = request.args.get('page', 1, type=int)
    
    query = Order.query.filter_by(order_type=OrderType.CATERING)
    
    if current_user.role.name == 'customer':
        query = query.filter_by(customer_id=current_user.id)
    
    catering_orders = query.order_by(Order.event_date.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('catering.html', catering_orders=catering_orders)


@app.route('/customers')
@login_required
@requires_role(['admin', 'manager', 'staff'])
def customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query.join(Role).filter(Role.name == 'customer')
    
    if search:
        query = query.filter(
            db.or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search)
            )
        )
    
    customers = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('customers.html', customers=customers, search=search)


@app.route('/staff')
@login_required
@requires_role(['admin', 'manager'])
def staff():
    page = request.args.get('page', 1, type=int)
    
    staff_members = User.query.join(Role).filter(Role.name == 'staff').paginate(page=page, per_page=20, error_out=False)
    
    # Get today's schedule
    today = date.today()
    today_schedule = StaffSchedule.query.filter_by(date=today).all()
    
    return render_template('staff.html', staff_members=staff_members, today_schedule=today_schedule)


@app.route('/reports')
@login_required
@requires_role(['admin', 'manager'])
def reports():
    # Generate various reports
    reports_data = {
        'sales_summary': {
            'total_orders': Order.query.count(),
            'total_revenue': sum([o.total_amount for o in Order.query.filter(Order.status != OrderStatus.CANCELLED).all()]),
            'average_order_value': 0,
            'cancelled_orders': Order.query.filter_by(status=OrderStatus.CANCELLED).count()
        },
        'inventory_summary': {
            'total_products': Product.query.filter_by(is_active=True).count(),
            'low_stock_items': len([inv for inv in Inventory.query.all() if inv.is_low_stock()]),
            'out_of_stock': Inventory.query.filter_by(quantity=0).count()
        }
    }
    
    # Calculate average order value
    total_orders = reports_data['sales_summary']['total_orders']
    if total_orders > 0:
        reports_data['sales_summary']['average_order_value'] = reports_data['sales_summary']['total_revenue'] / total_orders
    
    # Get AI insights for reports
    ai_insights = generate_ai_insights()
    
    return render_template('reports.html', reports_data=reports_data, ai_insights=ai_insights)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserForm(obj=current_user)
    
    if form.validate_on_submit():
        # Don't allow users to change their own role
        role_id = current_user.role_id
        form.populate_obj(current_user)
        current_user.role_id = role_id
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form)


@app.route('/api/order/<int:order_id>/status', methods=['POST'])
@login_required
@requires_role(['admin', 'manager', 'staff'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.json.get('status')
    
    try:
        order.status = OrderStatus(new_status)
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Order status updated successfully'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400


@app.route('/api/insights/refresh', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def refresh_insights():
    from ai_engine import SmartBakeryAI
    ai_engine = SmartBakeryAI()
    insights = ai_engine.generate_all_insights()
    return jsonify({'success': True, 'insights': len(insights)})


# PDF Generation Routes
@app.route('/download/invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check permissions
    if current_user.role.name not in ['admin', 'manager'] and order.customer_id != current_user.id:
        flash('You do not have permission to download this invoice.', 'error')
        return redirect(url_for('orders'))
    
    from pdf_generator import SmartBillGenerator
    pdf_generator = SmartBillGenerator()
    pdf_buffer = pdf_generator.generate_invoice_pdf(order_id)
    
    if pdf_buffer:
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'invoice_{order.order_number}.pdf',
            mimetype='application/pdf'
        )
    else:
        flash('Error generating invoice PDF.', 'error')
        return redirect(url_for('orders'))


@app.route('/download/daily-report')
@login_required
@requires_role(['admin', 'manager'])
def download_daily_report():
    report_date = request.args.get('date')
    if report_date:
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            report_date = date.today()
    else:
        report_date = date.today()
    
    from pdf_generator import SmartBillGenerator
    pdf_generator = SmartBillGenerator()
    pdf_buffer = pdf_generator.generate_daily_sales_report(report_date)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'daily_sales_report_{report_date.strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )


@app.route('/download/inventory-report')
@login_required
@requires_role(['admin', 'manager'])
def download_inventory_report():
    from pdf_generator import SmartBillGenerator
    pdf_generator = SmartBillGenerator()
    pdf_buffer = pdf_generator.generate_inventory_report()
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )


# Advanced AI Analytics Routes
@app.route('/ai-insights')
@login_required
@requires_role(['admin', 'manager'])
def ai_insights():
    insights = AIInsight.query.filter_by(is_active=True).order_by(AIInsight.created_at.desc()).all()
    
    # Group insights by type
    grouped_insights = {}
    for insight in insights:
        if insight.insight_type not in grouped_insights:
            grouped_insights[insight.insight_type] = []
        grouped_insights[insight.insight_type].append(insight)
    
    return render_template('ai_insights.html', grouped_insights=grouped_insights)


@app.route('/ai-insights/regenerate', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def regenerate_ai_insights():
    from ai_engine import SmartBakeryAI
    ai_engine = SmartBakeryAI()
    insights = ai_engine.generate_all_insights()
    
    flash(f'Generated {len(insights)} new AI insights!', 'success')
    return redirect(url_for('ai_insights'))


@app.route('/api/ai-insights/<insight_type>')
@login_required
@requires_role(['admin', 'manager'])
def get_ai_insights_api(insight_type):
    insights = AIInsight.query.filter_by(
        insight_type=insight_type,
        is_active=True
    ).order_by(AIInsight.created_at.desc()).limit(5).all()
    
    return jsonify([{
        'id': insight.id,
        'title': insight.title,
        'description': insight.description,
        'confidence_score': insight.confidence_score,
        'data': insight.data,
        'created_at': insight.created_at.isoformat()
    } for insight in insights])


# Product API for templates
@app.route('/api/products/<int:product_id>')
@login_required
def get_product_api(product_id):
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'cost': float(product.cost) if product.cost else None,
        'category': product.category.name if product.category else None,
        'inventory': {
            'quantity': product.inventory.quantity,
            'min_stock_level': product.inventory.min_stock_level,
            'max_stock_level': product.inventory.max_stock_level
        } if product.inventory else None
    })





@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
