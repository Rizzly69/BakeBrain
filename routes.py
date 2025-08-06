# --- All imports must be at the top ---
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, make_response, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, date, time
from app import app, db
from models import User, Product, Inventory, Order, OrderItem, Category, Role, StaffSchedule, ScheduleModification, AIInsight, OrderStatus, OrderType, Configuration, RawProduct, Notification, ProductRecipe, PurchaseOrder, EmailVerification, PasswordReset, UserSession
from forms import LoginForm, UserForm, ProductForm, InventoryForm, OrderForm, CategoryForm, ConfigurationForm, RawProductForm, ProductRecipeForm, SignupForm, EmailVerificationForm, ResendOTPForm, ForgotPasswordForm, ResetPasswordForm
from utils import generate_order_number, generate_ai_insights, requires_role, send_email_otp, send_password_reset_email, check_password_strength

# --- Detailed Analytics Page ---
@app.route('/detailed-analytics')
@login_required
@requires_role(['admin', 'manager'])
def detailed_analytics():
    return render_template('detailed_analytics.html')

# --- Dedicated AI Insights Page ---
@app.route('/ai-insights')
@login_required
@requires_role(['admin', 'manager'])
def ai_insights():
    # Get all active AI insights, ordered by most recent
    ai_insights = AIInsight.query.filter_by(is_active=True).order_by(AIInsight.created_at.desc()).all()
    # Group insights by type for the template
    grouped_insights = {}
    for insight in ai_insights:
        key = getattr(insight, 'insight_type', None) or (insight.get('insight_type') if isinstance(insight, dict) else None)
        if key not in grouped_insights:
            grouped_insights[key] = []
        grouped_insights[key].append(insight)
    return render_template('ai_insights.html', ai_insights=ai_insights, grouped_insights=grouped_insights)

# --- API: Staff details ---
@app.route('/api/staff/<int:staff_id>/details')
@login_required
@requires_role(['admin', 'manager'])
def staff_details_api(staff_id):
    staff_member = User.query.get_or_404(staff_id)
    if staff_member.role.name not in ['staff', 'manager']:
        return jsonify({'error': 'Not a staff/manager'}), 400
    data = {
        'id': staff_member.id,
        'first_name': staff_member.first_name,
        'last_name': staff_member.last_name,
        'email': staff_member.email,
        'phone': staff_member.phone,
        'role': staff_member.role.name,
        'active': staff_member.active,
    }
    return jsonify(data)

# --- API: Notifications ---
@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notif_list = [
        {
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
        } for n in notifications
    ]
    return jsonify({'notifications': notif_list, 'unread_count': unread_count})

@app.route('/api/notifications/mark_read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})
import logging

def track_schedule_modification(schedule, modification_type, old_data=None, reason=None):
    """Track schedule modifications for audit trail"""
    try:
        modification = ScheduleModification(
            schedule_id=schedule.id,
            modification_type=modification_type,
            modified_by=current_user.id,
            reason=reason
        )
        
        if modification_type == 'created':
            modification.new_start_time = schedule.start_time
            modification.new_end_time = schedule.end_time
            modification.new_position = schedule.position
            modification.new_notes = schedule.notes
        elif modification_type == 'updated' and old_data:
            modification.old_start_time = old_data.get('start_time')
            modification.old_end_time = old_data.get('end_time')
            modification.old_position = old_data.get('position')
            modification.old_notes = old_data.get('notes')
            modification.new_start_time = schedule.start_time
            modification.new_end_time = schedule.end_time
            modification.new_position = schedule.position
            modification.new_notes = schedule.notes
        elif modification_type == 'deleted':
            modification.old_start_time = schedule.start_time
            modification.old_end_time = schedule.end_time
            modification.old_position = schedule.position
            modification.old_notes = schedule.notes
        
        db.session.add(modification)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error tracking schedule modification: {e}")
        db.session.rollback()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


def get_device_info(user_agent):
    """Extract device information from user agent string"""
    ua = user_agent.lower()
    
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        if 'android' in ua:
            return 'Android Mobile'
        elif 'iphone' in ua:
            return 'iPhone'
        else:
            return 'Mobile Device'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'Tablet'
    elif 'windows' in ua:
        return 'Windows PC'
    elif 'mac' in ua or 'darwin' in ua:
        return 'Mac'
    elif 'linux' in ua:
        return 'Linux PC'
    else:
        return 'Desktop'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            user = User.query.filter_by(email=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return redirect(url_for('login'))
            
            # Check email verification only for new users
            # Existing users (who were migrated and have email_verified = True) can login directly
            # New users (who signed up after email verification was implemented) need verification
            if not user.email_verified:
                flash('Please verify your email address before logging in. Check your email for verification code.', 'warning')
                session['pending_verification_email'] = user.email
                return redirect(url_for('email_verification'))
            
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            
            # Create session record
            session_token = UserSession.generate_token()
            expires_at = datetime.utcnow() + timedelta(days=30) if form.remember_me.data else datetime.utcnow() + timedelta(hours=8)
            
            # Detect device info
            user_agent = request.headers.get('User-Agent', '')
            device_info = get_device_info(user_agent)
            
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=request.remote_addr,
                user_agent=user_agent,
                device_info=device_info,
                expires_at=expires_at
            )
            
            db.session.add(user_session)
            db.session.commit()
            
            # Set session token in response
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            
            response = make_response(redirect(next_page))
            response.set_cookie('session_token', session_token, max_age=30*24*60*60 if form.remember_me.data else 8*60*60)
            return response
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    # Terminate current session
    current_token = request.cookies.get('session_token', '')
    if current_token:
        user_session = UserSession.query.filter_by(
            session_token=current_token,
            user_id=current_user.id
        ).first()
        
        if user_session:
            user_session.is_active = False
            db.session.commit()
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token')
    return response


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
        
        # Chart data for orders status distribution
        order_status_data = {
            'pending': Order.query.filter_by(status=OrderStatus.PENDING).count(),
            'confirmed': Order.query.filter_by(status=OrderStatus.CONFIRMED).count(),
            'in_preparation': Order.query.filter_by(status=OrderStatus.IN_PREPARATION).count(),
            'ready': Order.query.filter_by(status=OrderStatus.READY).count(),
            'delivered': Order.query.filter_by(status=OrderStatus.DELIVERED).count()
        }
        
        # Revenue trend data (last 7 days)
        revenue_data = []
        labels = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            start_of_day = datetime.combine(date.date(), time.min)
            end_of_day = datetime.combine(date.date(), time.max)
            daily_revenue = sum([o.total_amount for o in Order.query.filter(
                Order.created_at >= start_of_day,
                Order.created_at <= end_of_day,
                Order.status != OrderStatus.CANCELLED
            ).all()])
            revenue_data.insert(0, float(daily_revenue))
            labels.insert(0, date.strftime('%m/%d'))
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_orders=recent_orders, 
                             ai_insights=ai_insights,
                             order_status_data=order_status_data,
                             revenue_data=revenue_data,
                             revenue_labels=labels)
    
    elif current_user.role.name == 'staff':
        # Staff dashboard - show their schedule and current orders
        today = date.today()
        schedule = StaffSchedule.query.filter_by(staff_id=current_user.id, date=today).first()
        active_orders = Order.query.filter(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION])).limit(10).all()
        
        # Staff-specific stats
        stats['active_orders'] = len(active_orders)
        stats['completed_today'] = Order.query.filter(
            Order.status == OrderStatus.DELIVERED,
            Order.created_at >= datetime.combine(today, time.min),
            Order.created_at <= datetime.combine(today, time.max)
        ).count()
        
        return render_template('dashboard_staff.html', schedule=schedule, active_orders=active_orders, stats=stats)
    
    elif current_user.role.name == 'customer':
        # Customer dashboard - show their orders
        customer_orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).limit(10).all()
        
        # Customer-specific stats
        stats['total_orders'] = len(customer_orders)
        stats['total_spent'] = sum([o.total_amount for o in customer_orders])
        stats['pending_orders'] = len([o for o in customer_orders if o.status == OrderStatus.PENDING])
        
        return render_template('dashboard_customer.html', customer_orders=customer_orders, stats=stats)
    
    else:  # baker role
        # Baker dashboard - show production orders and inventory
        production_orders = Order.query.filter(
            Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION])
        ).order_by(Order.created_at.desc()).limit(10).all()
        
        low_stock_items = [inv for inv in Inventory.query.all() if inv.is_low_stock()]
        
        # Baker-specific stats
        stats['production_orders'] = len(production_orders)
        stats['low_stock_items'] = len(low_stock_items)
        stats['completed_today'] = Order.query.filter(
            Order.status == OrderStatus.READY,
            Order.updated_at >= datetime.combine(date.today(), time.min),
            Order.updated_at <= datetime.combine(date.today(), time.max)
        ).count()
        
        return render_template('dashboard_baker.html', production_orders=production_orders, low_stock_items=low_stock_items, stats=stats)


@app.route('/inventory')
@login_required
@requires_role(['admin', 'manager', 'staff'])
def inventory():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    # Get finished products inventory
    query = db.session.query(Inventory).join(Product)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    inventory_items = query.paginate(page=page, per_page=20, error_out=False)
    low_stock_items = [inv for inv in Inventory.query.all() if inv.is_low_stock()]
    
    # Get raw products data
    raw_products = RawProduct.query.filter_by(is_active=True).all()
    low_stock_ingredients = [rp for rp in raw_products if rp.is_low_stock()]
    critical_ingredients = [rp for rp in raw_products if rp.is_critical_stock()]
    
    # Get all products for recipe analysis
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('inventory.html', 
                         inventory_items=inventory_items, 
                         low_stock_items=low_stock_items,
                         raw_products=raw_products,
                         low_stock_ingredients=low_stock_ingredients,
                         critical_ingredients=critical_ingredients,
                         products=products,
                         search=search)


@app.route('/inventory/update/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def update_inventory(id):
    inventory_item = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        quantity = request.form.get('quantity', type=int)
        min_stock = request.form.get('min_stock_level', type=int)
        max_stock = request.form.get('max_stock_level', type=int)
        
        if quantity is not None and min_stock is not None and max_stock is not None:
            inventory_item.quantity = quantity
            inventory_item.min_stock_level = min_stock
            inventory_item.max_stock_level = max_stock
            inventory_item.last_updated = datetime.utcnow()
            
            db.session.commit()
            flash('Inventory updated successfully!', 'success')
            return redirect(url_for('inventory'))
    
    return render_template('update_inventory.html', inventory_item=inventory_item)


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


@app.route('/categories')
@login_required
@requires_role(['admin', 'manager'])
def categories():
    """Manage product categories"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories.html', categories=categories)


@app.route('/categories/new', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def new_category():
    """Create a new category"""
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('categories'))
    
    return render_template('category_form.html', form=form, title='New Category')


@app.route('/products/new', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def new_product():
    try:
        form = ProductForm()
        
        # Check if we have categories
        if not form.category_id.choices:
            flash('No product categories found. Please create categories first.', 'error')
            return redirect(url_for('categories'))
        
        # Pre-select category if provided in URL
        category_id = request.args.get('category', type=int)
        if category_id:
            form.category_id.data = category_id
        
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
    
    except Exception as e:
        flash(f'Error creating product: {str(e)}', 'error')
        return redirect(url_for('products'))


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.cost = form.cost.data
        product.sku = form.sku.data
        product.category_id = form.category_id.data
        product.requires_preparation = form.requires_preparation.data
        product.preparation_time = form.preparation_time.data
        product.is_active = form.is_active.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('product_form.html', form=form, product=product, title='Edit Product')


@app.route('/products/<int:product_id>/recipe', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def manage_product_recipe(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductRecipeForm(product_id=product_id)
    
    if form.validate_on_submit():
        recipe = ProductRecipe(
            product_id=product_id,
            raw_product_id=form.raw_product_id.data,
            quantity_required=form.quantity_required.data,
            unit_of_measure=form.unit_of_measure.data
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Recipe ingredient added successfully!', 'success')
        return redirect(url_for('manage_product_recipe', product_id=product_id))
    
    # Get existing recipe
    recipes = ProductRecipe.query.filter_by(product_id=product_id).all()
    return render_template('product_recipe.html', product=product, form=form, recipes=recipes)


@app.route('/products/<int:product_id>/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def delete_recipe_ingredient(product_id, recipe_id):
    recipe = ProductRecipe.query.get_or_404(recipe_id)
    if recipe.product_id != product_id:
        flash('Invalid recipe!', 'error')
        return redirect(url_for('manage_product_recipe', product_id=product_id))
    
    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe ingredient removed successfully!', 'success')
    return redirect(url_for('manage_product_recipe', product_id=product_id))


@app.route('/api/products/<int:product_id>/max-quantity')
@login_required
def get_product_max_quantity(product_id):
    """API endpoint to get maximum orderable quantity for a product"""
    product = Product.query.get_or_404(product_id)
    max_quantity = product.get_max_orderable_quantity()
    return jsonify({
        'product_id': product_id,
        'max_quantity': max_quantity,
        'available_inventory': product.get_available_quantity(),
        'has_recipe': len(product.recipes) > 0
    })


@app.route('/raw-products')
@login_required
@requires_role(['admin', 'manager', 'staff'])
def raw_products():
    """View all raw products"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = RawProduct.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(RawProduct.name.contains(search))
    
    raw_products = query.order_by(RawProduct.name).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('raw_products.html', raw_products=raw_products, search=search)


@app.route('/raw-products/new', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def new_raw_product():
    """Create a new raw product"""
    form = RawProductForm()
    
    if form.validate_on_submit():
        raw_product = RawProduct(
            name=form.name.data,
            description=form.description.data,
            unit_of_measure=form.unit_of_measure.data,
            cost_per_unit=form.cost_per_unit.data,
            supplier=form.supplier.data,
            supplier_contact=form.supplier_contact.data,
            location=form.location.data or 'Storage',
            current_stock=form.current_stock.data,
            min_stock_level=form.min_stock_level.data,
            reorder_point=form.reorder_point.data,
            expiry_date=form.expiry_date.data,
            is_active=form.is_active.data
        )
        db.session.add(raw_product)
        db.session.commit()
        
        flash('Raw product created successfully!', 'success')
        return redirect(url_for('raw_products'))
    
    return render_template('raw_product_form.html', form=form, title='New Raw Product')


@app.route('/raw-products/<int:raw_product_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def edit_raw_product(raw_product_id):
    """Edit a raw product"""
    try:
        raw_product = RawProduct.query.get_or_404(raw_product_id)
        form = RawProductForm(obj=raw_product)
        
        if form.validate_on_submit():
            form.populate_obj(raw_product)
            raw_product.last_updated = datetime.utcnow()
            db.session.commit()
            
            flash('Raw product updated successfully!', 'success')
            return redirect(url_for('raw_products'))
        
        return render_template('raw_product_form.html', form=form, title='Edit Raw Product')
    
    except Exception as e:
        flash(f'Error updating raw product: {str(e)}', 'error')
        return redirect(url_for('raw_products'))


@app.route('/raw-products/<int:raw_product_id>/update-stock', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager', 'staff'])
def update_raw_product_stock(raw_product_id):
    """Update stock for a raw product"""
    raw_product = RawProduct.query.get_or_404(raw_product_id)
    
    if request.method == 'POST':
        new_stock = request.form.get('current_stock', type=float)
        if new_stock is not None:
            raw_product.current_stock = new_stock
            raw_product.last_updated = datetime.utcnow()
            if new_stock > raw_product.current_stock:
                raw_product.last_restocked = datetime.utcnow()
            db.session.commit()
            
            flash('Raw product stock updated successfully!', 'success')
            return redirect(url_for('raw_products'))
    
    return render_template('update_raw_product_stock.html', raw_product=raw_product)


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
        # Convert lowercase filter to uppercase to match enum values
        order_type_upper = order_type_filter.upper()
        try:
            query = query.filter_by(order_type=OrderType(order_type_upper))
        except ValueError:
            # If invalid order type, ignore the filter
            pass
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('orders.html', orders=orders, status_filter=status_filter, 
                         order_type_filter=order_type_filter)


@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
def new_order():
    form = OrderForm()
    
    # For customers, automatically set their ID and hide the customer selection
    if current_user.role.name == 'customer':
        form.customer_id.data = current_user.id
        form.customer_id.render_kw = {'style': 'display: none;'}
    else:
        # For staff/admin, populate customer choices
        customers = User.query.join(Role).filter(Role.name == 'customer').all()
        form.customer_id.choices = [(c.id, f"{c.first_name} {c.last_name}") for c in customers]
    
    if form.validate_on_submit():
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{Order.query.count() + 1:03d}"
        
        # For customers, use their own ID
        customer_id = current_user.id if current_user.role.name == 'customer' else form.customer_id.data
        
        # Convert string dates to datetime objects
        delivery_date = None
        event_date = None
        
        if form.delivery_date.data:
            try:
                delivery_date = datetime.strptime(form.delivery_date.data, '%Y-%m-%d %H:%M')
            except ValueError:
                flash('Invalid delivery date format. Please use YYYY-MM-DD HH:MM', 'error')
                return render_template('order_form.html', form=form, title='New Order')
        
        if form.event_date.data:
            try:
                event_date = datetime.strptime(form.event_date.data, '%Y-%m-%d %H:%M')
            except ValueError:
                flash('Invalid event date format. Please use YYYY-MM-DD HH:MM', 'error')
                return render_template('order_form.html', form=form, title='New Order')
        
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            order_type=OrderType(form.order_type.data),
            delivery_date=delivery_date,
            delivery_address=form.delivery_address.data,
            special_instructions=form.special_instructions.data,
            event_date=event_date,
            guest_count=form.guest_count.data,
            setup_requirements=form.setup_requirements.data,
            total_amount=0  # Will be calculated when items are added
        )
        db.session.add(order)
        db.session.commit()
        
        flash('Order created successfully! You can now add items to the order.', 'success')
        return redirect(url_for('orders'))
    
    return render_template('order_form.html', form=form, title='New Order')


@app.route('/orders/<int:order_id>/add_item', methods=['GET', 'POST'])
@login_required
def add_order_item(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check if user has permission to modify this order
    if current_user.role.name == 'customer' and order.customer_id != current_user.id:
        flash('You can only modify your own orders.', 'error')
        return redirect(url_for('orders'))
    
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', type=int)
        special_instructions = request.form.get('special_instructions', '').strip()
        
        if product_id and quantity:
            product = Product.query.get_or_404(product_id)
            
            # Check inventory availability
            max_available = product.get_max_orderable_quantity()
            if quantity > max_available:
                flash(f'Cannot order {quantity} {product.name}. Maximum available: {max_available}', 'error')
                return redirect(url_for('add_order_item', order_id=order_id))
            
            # Check if item already exists in order
            existing_item = OrderItem.query.filter_by(order_id=order.id, product_id=product_id).first()
            
            if existing_item:
                # Check if the new total quantity exceeds available inventory
                new_total_quantity = existing_item.quantity + quantity
                if new_total_quantity > max_available:
                    flash(f'Cannot add {quantity} more {product.name}. Total quantity would exceed available inventory.', 'error')
                    return redirect(url_for('add_order_item', order_id=order_id))
                
                existing_item.quantity = new_total_quantity
                existing_item.total_price = float(existing_item.unit_price) * existing_item.quantity
                if special_instructions:
                    existing_item.special_instructions = special_instructions
            else:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=float(product.price),
                    total_price=float(product.price) * quantity,
                    special_instructions=special_instructions if special_instructions else None
                )
                db.session.add(order_item)
            
            # Update order total
            order.total_amount = sum(item.total_price for item in order.items)
            db.session.commit()
            
            flash('Item added to order successfully!', 'success')
        
        return redirect(url_for('orders'))
    
    # GET request - show form
    products = Product.query.filter_by(is_active=True).all()
    return render_template('add_order_item.html', order=order, products=products)


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


@app.route('/customers/new', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def new_customer():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        password = request.form.get('password', 'customer123')  # Default password
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('new_customer'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('new_customer'))
        
        # Get customer role
        customer_role = Role.query.filter_by(name='customer').first()
        if not customer_role:
            customer_role = Role(name='customer', description='Customer with order access')
            db.session.add(customer_role)
            db.session.commit()
        
        # Create new customer
        customer = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role_id=customer_role.id
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash(f'Customer {first_name} {last_name} created successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('new_customer.html')


@app.route('/customers/<int:customer_id>')
@login_required
@requires_role(['admin', 'manager', 'staff'])
def customer_details(customer_id):
    """View customer details"""
    customer = User.query.get_or_404(customer_id)
    if customer.role.name != 'customer':
        flash('User is not a customer', 'error')
        return redirect(url_for('customers'))
    
    # Get customer's orders
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('customer_details.html', customer=customer, orders=orders)


@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def edit_customer(customer_id):
    """Edit customer information"""
    customer = User.query.get_or_404(customer_id)
    if customer.role.name != 'customer':
        flash('User is not a customer', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        customer.first_name = request.form.get('first_name')
        customer.last_name = request.form.get('last_name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.active = request.form.get('active') == 'on'
        
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=customer.email).first()
        if existing_user and existing_user.id != customer.id:
            flash('Email already exists!', 'error')
            return redirect(url_for('edit_customer', customer_id=customer.id))
        
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('edit_customer.html', customer=customer)


@app.route('/staff')
@login_required
@requires_role(['admin', 'manager'])
def staff():
    page = request.args.get('page', 1, type=int)
    
    # Get all staff and managers
    staff_members = User.query.join(Role).filter(Role.name.in_(['staff', 'manager'])).paginate(page=page, per_page=20, error_out=False)
    
    # Get today's schedule
    today = date.today()
    today_schedule = StaffSchedule.query.filter_by(date=today).all()
    
    return render_template('staff.html', staff_members=staff_members, today_schedule=today_schedule)


@app.route('/staff/new', methods=['GET', 'POST'])
@login_required
@requires_role(['admin'])
def new_staff():
    """Add new staff or manager (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        role = request.form.get('role')  # 'staff' or 'manager'
        password = request.form.get('password', 'staff123')  # Default password
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('new_staff'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('new_staff'))
        
        # Get role
        role_obj = Role.query.filter_by(name=role).first()
        if not role_obj:
            flash('Invalid role selected!', 'error')
            return redirect(url_for('new_staff'))
        
        # Create new staff/manager
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role_id=role_obj.id
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'{role.title()} {first_name} {last_name} created successfully!', 'success')
        return redirect(url_for('staff'))
    
    return render_template('new_staff.html')


@app.route('/staff/<int:staff_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_role(['admin'])
def edit_staff(staff_id):
    """Edit staff/manager information (admin only)"""
    staff_member = User.query.get_or_404(staff_id)
    
    # Only allow editing staff and managers
    if staff_member.role.name not in ['staff', 'manager']:
        flash('Can only edit staff and managers!', 'error')
        return redirect(url_for('staff'))
    
    if request.method == 'POST':
        staff_member.first_name = request.form.get('first_name')
        staff_member.last_name = request.form.get('last_name')
        staff_member.email = request.form.get('email')
        staff_member.phone = request.form.get('phone')
        staff_member.active = request.form.get('active') == 'on'
        
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=staff_member.email).first()
        if existing_user and existing_user.id != staff_member.id:
            flash('Email already exists!', 'error')
            return redirect(url_for('edit_staff', staff_id=staff_member.id))
        
        db.session.commit()
        flash('Staff member updated successfully!', 'success')
        return redirect(url_for('staff'))
    
    return render_template('edit_staff.html', staff_member=staff_member)


@app.route('/staff/<int:staff_id>/schedule', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def manage_staff_schedule(staff_id):
    """Manage staff schedule (staff cannot update their own schedule)"""
    staff_member = User.query.get_or_404(staff_id)
    # Only allow managing staff and managers
    if staff_member.role.name not in ['staff', 'manager']:
        flash('Can only manage schedules for staff and managers!', 'error')
        return redirect(url_for('staff'))
    # Restrict staff from updating their own schedule
    if current_user.role.name == 'staff':
        flash('Staff cannot update or change their own schedule.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            # Handle schedule deletion
            delete_date_str = request.form.get('delete_date')
            try:
                delete_date = datetime.strptime(delete_date_str, '%Y-%m-%d').date()
                schedule_to_delete = StaffSchedule.query.filter_by(
                    staff_id=staff_id,
                    date=delete_date
                ).first()
                if schedule_to_delete:
                    # Track deletion before removing
                    track_schedule_modification(schedule_to_delete, 'deleted', reason='Schedule deleted by manager')
                    db.session.delete(schedule_to_delete)
                    db.session.commit()
                    flash('Schedule deleted successfully!', 'success')
                else:
                    flash('Schedule not found!', 'error')
            except ValueError as e:
                flash(f'Invalid date format: {str(e)}', 'error')
            return redirect(url_for('manage_staff_schedule', staff_id=staff_id))
        # Handle schedule creation/update
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        position = request.form.get('position')
        notes = request.form.get('notes')
        try:
            schedule_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            # Check if schedule already exists for this date
            existing_schedule = StaffSchedule.query.filter_by(
                staff_id=staff_id, 
                date=schedule_date
            ).first()
            if existing_schedule:
                # Store old data for tracking
                old_data = {
                    'start_time': existing_schedule.start_time,
                    'end_time': existing_schedule.end_time,
                    'position': existing_schedule.position,
                    'notes': existing_schedule.notes
                }
                # Update existing schedule
                existing_schedule.start_time = start_time
                existing_schedule.end_time = end_time
                existing_schedule.position = position
                existing_schedule.notes = notes
                existing_schedule.is_modified = True
                existing_schedule.modification_reason = 'Schedule updated by manager'
                existing_schedule.modified_by = current_user.id
                # Track the modification
                track_schedule_modification(existing_schedule, 'updated', old_data, 'Schedule updated by manager')
            else:
                # Create new schedule
                schedule = StaffSchedule(
                    staff_id=staff_id,
                    date=schedule_date,
                    start_time=start_time,
                    end_time=end_time,
                    position=position,
                    notes=notes
                )
                db.session.add(schedule)
                db.session.flush()  # Get the ID
                # Track the creation
                track_schedule_modification(schedule, 'created', reason='Schedule created by manager')
            db.session.commit()
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('manage_staff_schedule', staff_id=staff_id))
        except ValueError as e:
            flash(f'Invalid date/time format: {str(e)}', 'error')
            return redirect(url_for('manage_staff_schedule', staff_id=staff_id))
    # Get current week's schedule
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    week_schedule = StaffSchedule.query.filter(
        StaffSchedule.staff_id == staff_id,
        StaffSchedule.date >= start_of_week,
        StaffSchedule.date <= end_of_week
    ).order_by(StaffSchedule.date, StaffSchedule.start_time).all()
    return render_template('manage_schedule.html', 
                         staff_member=staff_member, 
                         week_schedule=week_schedule,
                         start_of_week=start_of_week,
                         end_of_week=end_of_week,
                         timedelta=timedelta)


@app.route('/staff/schedule/weekly', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def weekly_schedule():
    """View and manage weekly schedule for all staff"""
    if request.method == 'POST':
        # Handle bulk schedule updates
        action = request.form.get('action')
        if action == 'bulk_update':
            # Process bulk schedule updates
            try:
                updates = request.form.getlist('schedule_updates[]')
                for update in updates:
                    data = json.loads(update)
                    staff_id = data.get('staff_id')
                    day = data.get('day')
                    start_time = data.get('start_time')
                    end_time = data.get('end_time')
                    position = data.get('position', 'General')
                    
                    if staff_id and day and start_time and end_time:
                        # Find existing schedule or create new one
                        schedule = StaffSchedule.query.filter_by(
                            staff_id=staff_id,
                            day_of_week=day
                        ).first()
                        
                        if schedule:
                            # Update existing schedule
                            old_data = {
                                'start_time': schedule.start_time,
                                'end_time': schedule.end_time,
                                'position': schedule.position
                            }
                            schedule.start_time = start_time
                            schedule.end_time = end_time
                            schedule.position = position
                            schedule.is_modified = True
                            
                            # Track modification
                            track_schedule_modification(schedule, 'updated', old_data, 'Bulk update')
                        else:
                            # Create new schedule
                            schedule = StaffSchedule(
                                staff_id=staff_id,
                                day_of_week=day,
                                start_time=start_time,
                                end_time=end_time,
                                position=position,
                                is_modified=True
                            )
                            db.session.add(schedule)
                            track_schedule_modification(schedule, 'created', reason='Bulk update')
                
                db.session.commit()
                flash('Bulk schedule updates applied successfully!', 'success')
            except Exception as e:
                flash(f'Error applying bulk updates: {str(e)}', 'error')
                db.session.rollback()
        
        return redirect(url_for('weekly_schedule'))
    
    # Get week parameter
    week_offset = request.args.get('week', 0, type=int)
    today = date.today()
    start_of_week = today + timedelta(weeks=week_offset) - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get all staff and managers
    staff_members = User.query.join(Role).filter(Role.name.in_(['staff', 'manager'])).all()
    
    # Get schedules for the week
    week_schedules = StaffSchedule.query.filter(
        StaffSchedule.date >= start_of_week,
        StaffSchedule.date <= end_of_week
    ).all()
    
    # Organize schedules by staff and date
    schedule_matrix = {}
    total_schedules = 0
    for staff in staff_members:
        schedule_matrix[staff.id] = {}
        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            schedule_matrix[staff.id][current_date] = None
    
    for schedule in week_schedules:
        if schedule.staff_id in schedule_matrix:
            schedule_matrix[schedule.staff_id][schedule.date] = schedule
            total_schedules += 1
    
    return render_template('weekly_schedule.html',
                         staff_members=staff_members,
                         schedule_matrix=schedule_matrix,
                         start_of_week=start_of_week,
                         end_of_week=end_of_week,
                         week_offset=week_offset,
                         total_schedules=total_schedules,
                         timedelta=timedelta)


@app.route('/modifications')
@login_required
@requires_role(['admin', 'manager'])
def modifications():
    """View schedule modifications"""
    # Get filter parameters
    staff_id = request.args.get('staff_id', type=int)
    modification_type = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = ScheduleModification.query.join(StaffSchedule).join(User, StaffSchedule.staff_id == User.id)
    
    if staff_id:
        query = query.filter(StaffSchedule.staff_id == staff_id)
    
    if modification_type:
        query = query.filter(ScheduleModification.modification_type == modification_type)
    
    if date_from:
        query = query.filter(ScheduleModification.modified_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(ScheduleModification.modified_at <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
    
    # Get paginated results
    modifications = query.order_by(ScheduleModification.modified_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get statistics
    total_modifications = ScheduleModification.query.count()
    created_count = ScheduleModification.query.filter_by(modification_type='created').count()
    updated_count = ScheduleModification.query.filter_by(modification_type='updated').count()
    deleted_count = ScheduleModification.query.filter_by(modification_type='deleted').count()
    
    # Get all staff for filter dropdown
    staff_members = User.query.join(Role).filter(Role.name.in_(['staff', 'manager'])).all()
    
    return render_template('modifications.html',
                         modifications=modifications,
                         staff_members=staff_members,
                         total_modifications=total_modifications,
                         created_count=created_count,
                         updated_count=updated_count,
                         deleted_count=deleted_count)


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
    
    # Show all active AI insights for reports
    ai_insights = AIInsight.query.filter_by(is_active=True).order_by(AIInsight.created_at.desc()).all()
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
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status in [status.value for status in OrderStatus]:
        old_status = order.status
        order.status = OrderStatus(new_status)
        order.updated_at = datetime.utcnow()
        
        # If order is being confirmed, decrease inventory and consume raw materials
        if new_status == 'CONFIRMED' and old_status != OrderStatus.CONFIRMED:
            try:
                # Process each item in the order
                for item in order.items:
                    product = item.product
                    quantity = item.quantity
                    
                    # Check if product has inventory
                    inventory = Inventory.query.filter_by(product_id=product.id).first()
                    
                    if inventory:
                        # Check if we have enough inventory
                        if inventory.quantity >= quantity:
                            # Decrease inventory
                            inventory.quantity -= quantity
                            inventory.last_updated = datetime.utcnow()
                        else:
                            # Not enough inventory
                            db.session.rollback()
                            return jsonify({
                                'success': False, 
                                'message': f'Insufficient inventory for {product.name}. Available: {inventory.quantity}, Required: {quantity}'
                            }), 400
                    else:
                        # No inventory record found - check if we can make it from raw materials
                        if product.recipes:
                            # Check if we have enough raw materials to make the product
                            if not product.can_make_quantity(quantity):
                                db.session.rollback()
                                return jsonify({
                                    'success': False, 
                                    'message': f'Insufficient raw materials to make {product.name}'
                                }), 400
                            
                            # Consume raw materials
                            if not product.consume_raw_materials(quantity):
                                db.session.rollback()
                                return jsonify({
                                    'success': False, 
                                    'message': f'Failed to consume raw materials for {product.name}'
                                }), 400
                        else:
                            # No inventory and no recipe
                            db.session.rollback()
                            return jsonify({
                                'success': False, 
                                'message': f'No inventory record found for {product.name}'
                            }), 400
                
                db.session.commit()
                return jsonify({'success': True, 'message': f'Order confirmed and inventory updated successfully'})
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Error updating inventory: {str(e)}'}), 500
        
        # If order is being cancelled and was previously confirmed, restore inventory and raw materials
        elif new_status == 'CANCELLED' and old_status == OrderStatus.CONFIRMED:
            try:
                # Process each item in the order to restore inventory
                for item in order.items:
                    product = item.product
                    quantity = item.quantity
                    
                    # Check if product has inventory
                    inventory = Inventory.query.filter_by(product_id=product.id).first()
                    
                    if inventory:
                        # Restore inventory
                        inventory.quantity += quantity
                        inventory.last_updated = datetime.utcnow()
                    else:
                        # Create inventory record if it doesn't exist
                        inventory = Inventory(
                            product_id=product.id,
                            quantity=quantity,
                            min_stock_level=10,
                            max_stock_level=100,
                            last_updated=datetime.utcnow()
                        )
                        db.session.add(inventory)
                    
                    # Restore raw materials if product has recipe
                    if product.recipes:
                        if not product.restore_raw_materials(quantity):
                            db.session.rollback()
                            return jsonify({
                                'success': False, 
                                'message': f'Failed to restore raw materials for {product.name}'
                            }), 400
                
                db.session.commit()
                return jsonify({'success': True, 'message': f'Order cancelled and inventory restored successfully'})
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Error restoring inventory: {str(e)}'}), 500
        else:
            # For other status changes, just update the status
            db.session.commit()
            return jsonify({'success': True, 'message': f'Order status updated to {new_status}'})
    else:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400


@app.route('/api/order/<int:order_id>/details')
@login_required
def get_order_details(order_id):
    """Get detailed order information for modal display"""
    order = Order.query.get_or_404(order_id)
    
    # Check if user has permission to view this order
    if current_user.role.name == 'customer' and order.customer_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    html = render_template('components/order_details.html', order=order)
    return jsonify({'html': html})


@app.route('/api/insights/refresh', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def refresh_insights():
    generate_ai_insights()
    flash('AI insights refreshed successfully!', 'success')
    return jsonify({'success': True})


# PDF Generation Routes
@app.route('/download/invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    try:
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
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('orders'))


@app.route('/download/daily-report')
@login_required
@requires_role(['admin', 'manager'])
def download_daily_report():
    try:
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
    except Exception as e:
        flash(f'Error generating daily report PDF: {str(e)}', 'error')
        return redirect(url_for('reports'))


@app.route('/download/inventory-report')
@login_required
@requires_role(['admin', 'manager'])
def download_inventory_report():
    try:
        from pdf_generator import SmartBillGenerator
        pdf_generator = SmartBillGenerator()
        pdf_buffer = pdf_generator.generate_inventory_report()
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating inventory report PDF: {str(e)}', 'error')
        return redirect(url_for('reports'))


@app.route('/download/sales-summary')
@login_required
@requires_role(['admin', 'manager'])
def download_sales_summary():
    try:
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
            download_name=f'sales_summary_{report_date.strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating sales summary PDF: {str(e)}', 'error')
        return redirect(url_for('reports'))


# Advanced AI Analytics Routes



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

@app.route('/ai-insights/regenerate', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def regenerate_insights():
    """Regenerate all AI insights with fresh data"""
    try:
        # Clear existing insights
        AIInsight.query.filter_by(is_active=True).update({'is_active': False})
        db.session.commit()
        
        # Generate new insights
        generate_ai_insights()
        
        # Also generate advanced ML insights
        from ai_engine import SmartBakeryAI
        ai_engine = SmartBakeryAI()
        ml_insights = ai_engine.generate_all_insights()
        
        flash('AI insights regenerated successfully!', 'success')
        return jsonify({'success': True, 'message': 'Insights regenerated successfully'})
    except Exception as e:
        flash(f'Error regenerating insights: {str(e)}', 'error')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai-insights/<int:insight_id>/dismiss', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def dismiss_insight(insight_id):
    """Dismiss an AI insight"""
    try:
        insight = AIInsight.query.get_or_404(insight_id)
        insight.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Insight dismissed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai-insights/<int:insight_id>/implement', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def implement_insight(insight_id):
    """Implement an AI insight action"""
    try:
        insight = AIInsight.query.get_or_404(insight_id)
        
        # Parse the insight data to determine what action to take
        if insight.insight_type == 'demand_forecast':
            # Implement demand forecast by updating inventory levels
            data = insight.data if isinstance(insight.data, dict) else json.loads(insight.data)
            if 'product_id' in data:
                product = Product.query.get(data['product_id'])
                if product:
                    # Increase inventory based on forecast
                    inventory = Inventory.query.filter_by(product_id=product.id).first()
                    if inventory:
                        forecast_demand = data.get('predicted_daily_demand', 0)
                        inventory.quantity = max(inventory.quantity, int(forecast_demand * 3))  # 3 days buffer
                        db.session.commit()
                        return jsonify({'success': True, 'message': f'Inventory updated for {product.name} based on forecast'})
        
        elif insight.insight_type == 'inventory_optimization':
            # Implement inventory optimization
            data = insight.data if isinstance(insight.data, dict) else json.loads(insight.data)
            if 'products' in data:
                for product_name in data['products']:
                    product = Product.query.filter_by(name=product_name).first()
                    if product:
                        inventory = Inventory.query.filter_by(product_id=product.id).first()
                        if inventory and inventory.quantity < inventory.min_stock_level:
                            inventory.quantity = inventory.min_stock_level * 2
                db.session.commit()
                return jsonify({'success': True, 'message': 'Inventory levels optimized'})
        
        elif insight.insight_type == 'peak_hours_analysis':
            # Implement peak hours optimization
            data = insight.data if isinstance(insight.data, dict) else json.loads(insight.data)
            peak_hour = data.get('peak_hour', 12)
            # Create a notification for staff scheduling
            notification = Notification(
                user_id=current_user.id,
                message=f'Peak hours identified at {peak_hour}:00. Consider adjusting staff schedules.',
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Staff scheduling recommendation created'})
        
        return jsonify({'success': True, 'message': 'Insight implemented successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/analytics/customers')
@login_required
@requires_role(['admin', 'manager'])
def customer_analytics():
    """Get customer analytics data"""
    try:
        # Get top customers by total spent
        top_customers = db.session.query(
            User.first_name, User.last_name,
            db.func.sum(Order.total_amount).label('total_spent')
        ).join(Order, User.id == Order.customer_id)\
         .filter(Order.status != OrderStatus.CANCELLED)\
         .group_by(User.id)\
         .order_by(db.func.sum(Order.total_amount).desc())\
         .limit(5).all()
        
        # Calculate retention rate (customers with multiple orders)
        total_customers = User.query.join(Role).filter(Role.name == 'customer').count()
        repeat_customers = db.session.query(Order.customer_id)\
            .group_by(Order.customer_id)\
            .having(db.func.count(Order.id) > 1)\
            .count()
        
        retention_rate = round((repeat_customers / total_customers * 100) if total_customers > 0 else 0, 1)
        
        return jsonify({
            'top_customers': [
                {
                    'name': f"{customer.first_name} {customer.last_name}",
                    'total_spent': float(customer.total_spent)
                } for customer in top_customers
            ],
            'retention_rate': retention_rate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/products')
@login_required
@requires_role(['admin', 'manager'])
def product_analytics():
    """Get product analytics data"""
    try:
        # Get top products by sales count
        top_products = db.session.query(
            Product.name,
            db.func.sum(OrderItem.quantity).label('sales_count')
        ).join(OrderItem, Product.id == OrderItem.product_id)\
         .join(Order, OrderItem.order_id == Order.id)\
         .filter(Order.status != OrderStatus.CANCELLED)\
         .group_by(Product.id)\
         .order_by(db.func.sum(OrderItem.quantity).desc())\
         .limit(5).all()
        
        # Calculate total revenue
        total_revenue = db.session.query(db.func.sum(Order.total_amount))\
            .filter(Order.status != OrderStatus.CANCELLED)\
            .scalar() or 0
        
        return jsonify({
            'top_products': [
                {
                    'name': product.name,
                    'sales_count': int(product.sales_count)
                } for product in top_products
            ],
            'total_revenue': float(total_revenue)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/predictive')
@login_required
@requires_role(['admin', 'manager'])
def predictive_analytics():
    """Get predictive analytics data"""
    try:
        # Generate demand forecast using AI engine
        from ai_engine import SmartBakeryAI
        ai_engine = SmartBakeryAI()
        ml_insights = ai_engine.demand_forecasting_ml()
        
        # Extract demand forecast data
        demand_forecast = []
        for insight in ml_insights:
            if insight.insight_type == 'ml_demand_forecast':
                data = insight.data if isinstance(insight.data, dict) else json.loads(insight.data)
                product = Product.query.get(data.get('product_id'))
                if product:
                    demand_forecast.append({
                        'product': product.name,
                        'predicted_demand': round(data.get('predicted_daily_demand', 0), 1)
                    })
        
        # Determine trend direction based on recent sales
        recent_orders = Order.query.filter(
            Order.created_at >= datetime.now() - timedelta(days=30),
            Order.status != OrderStatus.CANCELLED
        ).all()
        
        if len(recent_orders) >= 2:
            # Simple trend analysis
            first_half = sum([o.total_amount for o in recent_orders[:len(recent_orders)//2]])
            second_half = sum([o.total_amount for o in recent_orders[len(recent_orders)//2:]])
            
            if second_half > first_half:
                trend_direction = "↗️ Increasing"
            elif second_half < first_half:
                trend_direction = "↘️ Decreasing"
            else:
                trend_direction = "→ Stable"
        else:
            trend_direction = "→ Insufficient Data"
        
        return jsonify({
            'demand_forecast': demand_forecast,
            'trend_direction': trend_direction
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chart-data')
@login_required
@requires_role(['admin', 'manager'])
def get_chart_data():
    """Get dynamic chart data based on time period"""
    period = request.args.get('period', '7d')  # 7d, 30d, 90d, 1y
    
    # Parse period
    if period == '7d':
        days = 7
        date_format = '%m/%d'
    elif period == '30d':
        days = 30
        date_format = '%m/%d'
    elif period == '90d':
        days = 90
        date_format = '%m/%d'
    elif period == '1y':
        days = 365
        date_format = '%m/%Y'
    else:
        days = 7
        date_format = '%m/%d'
    

    # Generate revenue data
    revenue_data = []
    labels = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        start_of_day = datetime.combine(date.date(), time.min)
        end_of_day = datetime.combine(date.date(), time.max)
        daily_revenue = sum([o.total_amount for o in Order.query.filter(
            Order.created_at >= start_of_day,
            Order.created_at <= end_of_day,
            Order.status != OrderStatus.CANCELLED
        ).all()])
        revenue_data.insert(0, float(daily_revenue))
        labels.insert(0, date.strftime(date_format))

    # Revenue by category (for donut chart)
    from collections import defaultdict
    category_totals = defaultdict(float)
    orders = Order.query.filter(Order.status != OrderStatus.CANCELLED).all()
    for order in orders:
        for item in order.items:
            if item.product and item.product.category:
                category_totals[item.product.category.name] += float(item.total_price)
    donut = {
        'labels': list(category_totals.keys()),
        'data': list(category_totals.values())
    } if category_totals else {'labels': [], 'data': []}

    # Generate order status data filtered by time period
    start_date = datetime.now() - timedelta(days=days)
    order_status_data = {
        'pending': Order.query.filter(
            Order.status == OrderStatus.PENDING,
            Order.created_at >= start_date
        ).count(),
        'confirmed': Order.query.filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.created_at >= start_date
        ).count(),
        'in_preparation': Order.query.filter(
            Order.status == OrderStatus.IN_PREPARATION,
            Order.created_at >= start_date
        ).count(),
        'ready': Order.query.filter(
            Order.status == OrderStatus.READY,
            Order.created_at >= start_date
        ).count(),
        'delivered': Order.query.filter(
            Order.status == OrderStatus.DELIVERED,
            Order.created_at >= start_date
        ).count()
    }

    # Statistical analysis (regression, ANOVA, z-test, p-value)
    regression = {}
    anova_result = None
    z_test_result = None
    p_value = None
    try:
        import numpy as np
        from scipy import stats
        x = np.arange(len(revenue_data))
        y = np.array(revenue_data)
        if len(x) > 1 and np.any(y):
            slope, intercept, r_value, p_val, std_err = stats.linregress(x, y)
            regression = {
                'slope': slope,
                'intercept': intercept,
                'r2': r_value ** 2,
                'equation': f'y = {slope:.2f}x + {intercept:.2f}'
            }
            # ANOVA (one-way, using revenue by week if possible)
            if len(y) >= 14:
                week1 = y[:len(y)//2]
                week2 = y[len(y)//2:]
                f_val, anova_p = stats.f_oneway(week1, week2)
                anova_result = f'F={f_val:.2f}, p={anova_p:.3f}'
            # Z-test (compare first and last day)
            if len(y) > 1:
                z = (y[-1] - y[0]) / (np.std(y) / np.sqrt(len(y))) if np.std(y) > 0 else 0
                z_test_result = f'z={z:.2f}'
                p_value = float(stats.norm.sf(abs(z)) * 2)  # two-tailed
    except Exception as e:
        regression = {}

    return jsonify({
        'revenue_data': revenue_data,
        'revenue_labels': labels,
        'order_status_data': order_status_data,
        'donut': donut,
        'regression': regression,
        'anova': anova_result,
        'z_test': z_test_result,
        'p_value': p_value,
        'period': period
    })


# Product API for templates
@app.route('/api/products/<int:product_id>')
@login_required
def get_product_api(product_id):
    """API endpoint to get product details"""
    product = Product.query.get_or_404(product_id)
    inventory = Inventory.query.filter_by(product_id=product.id).first()
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'description': product.description,
        'requires_preparation': product.requires_preparation,
        'preparation_time': product.preparation_time,
        'category': product.category.name if product.category else None,
        'inventory': {
            'quantity': inventory.quantity if inventory else 0,
            'min_stock_level': inventory.min_stock_level if inventory else 0
        } if inventory else None
    })

@app.route('/api/inventory/<int:inventory_id>/quick-restock', methods=['POST'])
@login_required
@requires_role(['admin', 'manager', 'staff'])
def quick_restock_inventory(inventory_id):
    """Quick restock inventory item"""
    try:
        data = request.get_json()
        quantity = data.get('quantity', 0)
        
        if not quantity or quantity <= 0:
            return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
        
        inventory = Inventory.query.get_or_404(inventory_id)
        old_quantity = inventory.quantity
        inventory.quantity += quantity
        inventory.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Added {quantity} units to inventory. New total: {inventory.quantity}',
            'new_quantity': inventory.quantity
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/raw-materials/order', methods=['POST'])
@login_required
@requires_role(['admin', 'manager', 'staff'])
def order_raw_material():
    """Place order for raw materials"""
    try:
        data = request.get_json()
        material_name = data.get('material_name')
        supplier_contact = data.get('supplier_contact')
        quantity = data.get('quantity', 0)
        
        if not material_name or not supplier_contact or not quantity:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Find the raw material
        raw_material = RawProduct.query.filter_by(name=material_name).first()
        if not raw_material:
            return jsonify({'success': False, 'message': 'Raw material not found'}), 404
        
        # Create a purchase order record (in a real system, this would be more complex)
        purchase_order = PurchaseOrder(
            raw_product_id=raw_material.id,
            quantity=quantity,
            supplier_contact=supplier_contact,
            ordered_by=current_user.id,
            status='pending',
            order_date=datetime.utcnow()
        )
        db.session.add(purchase_order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Order placed for {quantity} units of {material_name}',
            'order_id': purchase_order.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/configuration')
@login_required
@requires_role(['admin', 'manager'])
def configuration():
    """Configuration management page"""
    category = request.args.get('category', 'company')
    configs = Configuration.query.filter_by(category=category).order_by(Configuration.key).all()
    
    # Get all available categories
    categories = db.session.query(Configuration.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('configuration.html', 
                         configs=configs, 
                         categories=categories, 
                         current_category=category)


@app.route('/configuration/edit/<int:config_id>', methods=['GET', 'POST'])
@login_required
@requires_role(['admin', 'manager'])
def edit_configuration(config_id):
    """Edit a configuration item"""
    config = Configuration.query.get_or_404(config_id)
    
    if not config.is_editable:
        flash('This configuration item cannot be edited.', 'error')
        return redirect(url_for('configuration'))
    
    form = ConfigurationForm(config_item=config)
    
    if request.method == 'GET':
        form.value.data = config.get_typed_value()
        form.description.data = config.description
    
    if form.validate_on_submit():
        try:
            # Update the configuration value
            config.value = str(form.value.data)
            config.description = form.description.data
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Configuration updated successfully!', 'success')
            return redirect(url_for('configuration', category=config.category))
        except Exception as e:
            flash(f'Error updating configuration: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('edit_configuration.html', form=form, config=config)


@app.route('/configuration/reset/<int:config_id>', methods=['POST'])
@login_required
@requires_role(['admin'])
def reset_configuration(config_id):
    """Reset a configuration item to default value"""
    config = Configuration.query.get_or_404(config_id)
    
    # Define default values
    default_values = {
        'company_name': 'Smart Bakery Manager',
        'company_tagline': 'Premium Artisan Bakery',
        'company_address': '123 Baker Street, Bakery District',
        'company_phone': '(555) 123-BAKE',
        'company_email': 'orders@smartbakery.com',
        'company_website': 'www.smartbakery.com',
        'tax_rate': '8.5',
        'currency_symbol': '$',
        'delivery_fee': '5.00',
        'free_delivery_threshold': '50.00',
        'catering_deposit_percentage': '25',
        'catering_setup_fee': '25.00',
        'default_min_stock': '10',
        'default_max_stock': '100',
        'low_stock_threshold': '5',
    }
    
    if config.key in default_values:
        config.value = default_values[config.key]
        config.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Configuration reset to default value!', 'success')
    else:
        flash('No default value available for this configuration.', 'error')
    
    return redirect(url_for('configuration', category=config.category))


@app.route('/configuration/bulk_update', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def bulk_update_configuration():
    """Bulk update configuration values"""
    try:
        updates = request.get_json()
        for key, value in updates.items():
            config = Configuration.query.filter_by(key=key).first()
            if config and config.is_editable:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Configuration updated successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating configuration: {str(e)}'})


@app.route('/api/configuration/<key>')
@login_required
def get_configuration_api(key):
    """API endpoint to get configuration value"""
    value = Configuration.get_value(key)
    return jsonify({'key': key, 'value': value})


@app.route('/api/schedule/restore/<int:modification_id>', methods=['POST'])
@login_required
@requires_role(['admin', 'manager'])
def restore_schedule(modification_id):
    """Restore a deleted schedule"""
    try:
        modification = ScheduleModification.query.get_or_404(modification_id)
        
        if modification.modification_type != 'deleted':
            return jsonify({'success': False, 'message': 'Can only restore deleted schedules'})
        
        # Create new schedule with the old data
        new_schedule = StaffSchedule(
            staff_id=modification.schedule.staff_id,
            date=modification.schedule.date,
            start_time=modification.old_start_time,
            end_time=modification.old_end_time,
            position=modification.old_position,
            notes=modification.old_notes,
            is_modified=True,
            modification_reason=f"Restored from deletion by {current_user.first_name} {current_user.last_name}",
            modified_by=current_user.id
        )
        
        db.session.add(new_schedule)
        
        # Create modification record for restoration
        restoration_mod = ScheduleModification(
            schedule_id=new_schedule.id,
            modification_type='created',
            new_start_time=modification.old_start_time,
            new_end_time=modification.old_end_time,
            new_position=modification.old_position,
            new_notes=modification.old_notes,
            reason=f"Restored from deletion (original mod: {modification_id})",
            modified_by=current_user.id
        )
        
        db.session.add(restoration_mod)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Schedule restored successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/schedule/<int:schedule_id>/modifications')
@login_required
@requires_role(['admin', 'manager'])
def get_schedule_modifications(schedule_id):
    """Get modification history for a specific schedule"""
    try:
        modifications = ScheduleModification.query.filter_by(schedule_id=schedule_id)\
            .order_by(ScheduleModification.created_at.desc()).all()
        
        return jsonify({
            'modifications': [{
                'id': mod.id,
                'modification_type': mod.modification_type,
                'created_at': mod.created_at.strftime('%Y-%m-%d %H:%M'),
                'changes': get_modification_changes(mod),
                'reason': mod.reason
            } for mod in modifications]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_modification_changes(modification):
    """Helper function to format modification changes"""
    changes = []
    
    if modification.modification_type == 'created':
        changes.append(f"Created: {modification.new_start_time}-{modification.new_end_time}")
    elif modification.modification_type == 'updated':
        if modification.old_start_time != modification.new_start_time:
            changes.append(f"Start: {modification.old_start_time} → {modification.new_start_time}")
        if modification.old_end_time != modification.new_end_time:
            changes.append(f"End: {modification.old_end_time} → {modification.new_end_time}")
        if modification.old_position != modification.new_position:
            changes.append(f"Position: {modification.old_position} → {modification.new_position}")
    elif modification.modification_type == 'deleted':
        changes.append(f"Deleted: {modification.old_start_time}-{modification.old_end_time}")
    
    return '; '.join(changes)

@app.route('/api/modifications/export')
@login_required
@requires_role(['admin', 'manager'])
def export_modifications():
    """Export modifications to CSV"""
    try:
        import csv
        from io import StringIO
        
        # Get filter parameters
        staff_id = request.args.get('staff_id', type=int)
        modification_type = request.args.get('type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = ScheduleModification.query.join(StaffSchedule).join(User, StaffSchedule.staff_id == User.id)
        
        if staff_id:
            query = query.filter(StaffSchedule.staff_id == staff_id)
        
        if modification_type:
            query = query.filter(ScheduleModification.modification_type == modification_type)
        
        if date_from:
            query = query.filter(ScheduleModification.modified_at >= datetime.strptime(date_from, '%Y-%m-%d'))
        
        if date_to:
            query = query.filter(ScheduleModification.modified_at <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
        
        modifications = query.order_by(ScheduleModification.modified_at.desc()).all()
        
        # Create CSV
        si = StringIO()
        cw = csv.writer(si)
        
        # Write header
        cw.writerow([
            'Date', 'Time', 'Staff Member', 'Schedule Date', 'Modification Type',
            'Old Start Time', 'Old End Time', 'Old Position', 'Old Notes',
            'New Start Time', 'New End Time', 'New Position', 'New Notes',
            'Reason', 'Modified By', 'Modifier Role'
        ])
        
        # Write data
        for mod in modifications:
            cw.writerow([
                mod.modified_at.strftime('%Y-%m-%d'),
                mod.modified_at.strftime('%H:%M:%S'),
                f"{mod.schedule.staff_member.first_name} {mod.schedule.staff_member.last_name}",
                mod.schedule.date.strftime('%Y-%m-%d'),
                mod.modification_type.title(),
                mod.old_start_time.strftime('%H:%M') if mod.old_start_time else '',
                mod.old_end_time.strftime('%H:%M') if mod.old_end_time else '',
                mod.old_position or '',
                mod.old_notes or '',
                mod.new_start_time.strftime('%H:%M') if mod.new_start_time else '',
                mod.new_end_time.strftime('%H:%M') if mod.new_end_time else '',
                mod.new_position or '',
                mod.new_notes or '',
                mod.reason or '',
                f"{mod.modifier.first_name} {mod.modifier.last_name}",
                mod.modifier.role.name.title()
            ])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=schedule_modifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output.headers["Content-type"] = "text/csv"
        return output
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.route('/customer-ai-insights')
@login_required
def customer_ai_insights():
    """AI insights and recommendations for customers"""
    if current_user.role.name != 'customer':
        flash('This page is only for customers.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get customer's order history
    customer_orders = Order.query.filter_by(customer_id=current_user.id).all()
    
    # Generate personalized recommendations
    recommendations = []
    
    # Popular items recommendation
    popular_products = db.session.query(Product, db.func.count(OrderItem.id).label('order_count'))\
        .join(OrderItem)\
        .join(Order)\
        .filter(Order.status != OrderStatus.CANCELLED)\
        .group_by(Product.id)\
        .order_by(db.func.count(OrderItem.id).desc())\
        .limit(5).all()
    
    if popular_products:
        recommendations.append({
            'type': 'trending',
            'title': 'Trending Items',
            'description': 'Our most popular items this week',
            'items': [{'name': p[0].name, 'price': p[0].price, 'description': p[0].description} for p in popular_products]
        })
    
    # Seasonal recommendations
    current_month = datetime.now().month
    seasonal_items = []
    if current_month in [12, 1, 2]:  # Winter
        seasonal_items = ['Hot Chocolate', 'Warm Bread', 'Comfort Pastries']
    elif current_month in [3, 4, 5]:  # Spring
        seasonal_items = ['Fresh Fruit Tarts', 'Light Cakes', 'Spring Pastries']
    elif current_month in [6, 7, 8]:  # Summer
        seasonal_items = ['Iced Coffee', 'Fruit Pies', 'Light Desserts']
    else:  # Fall
        seasonal_items = ['Pumpkin Spice Items', 'Warm Pies', 'Autumn Cakes']
    
    recommendations.append({
        'type': 'seasonal',
        'title': 'Seasonal Favorites',
        'description': f'Perfect for {["Winter", "Spring", "Summer", "Fall"][(current_month % 12) // 3]}',
        'items': [{'name': item, 'description': f'Delicious {item.lower()} perfect for the season'} for item in seasonal_items]
    })
    
    # Personalized recommendations based on order history
    if customer_orders:
        # Get customer's favorite categories
        customer_categories = db.session.query(Category, db.func.count(OrderItem.id).label('count'))\
            .join(Product)\
            .join(OrderItem)\
            .join(Order)\
            .filter(Order.customer_id == current_user.id)\
            .group_by(Category.id)\
            .order_by(db.func.count(OrderItem.id).desc())\
            .limit(3).all()
        
        if customer_categories:
            recommendations.append({
                'type': 'personalized',
                'title': 'Based on Your Preferences',
                'description': 'Items you might love based on your order history',
                'items': [{'name': cat[0].name, 'description': f'You\'ve ordered {cat[0].name.lower()} {cat[1]} times'} for cat in customer_categories]
            })
    
    # AI-powered tips
    ai_tips = [
        {
            'title': 'Order Timing Tip',
            'description': 'Orders placed before 2 PM are guaranteed same-day pickup for regular items.',
            'icon': 'clock'
        },
        {
            'title': 'Catering Planning',
            'description': 'For events with 20+ guests, we recommend placing orders at least 3 days in advance.',
            'icon': 'calendar'
        },
        {
            'title': 'Custom Orders',
            'description': 'Need something special? Custom cakes and pastries require 48 hours notice.',
            'icon': 'star'
        }
    ]
    
    return render_template('customer_ai_insights.html', 
                         recommendations=recommendations, 
                         ai_tips=ai_tips,
                         customer_orders=customer_orders)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration with email verification"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = SignupForm()
    if form.validate_on_submit():
        # Check password strength
        strength_check = check_password_strength(form.password.data)
        if strength_check['score'] < 3:
            flash('Password is too weak. Please choose a stronger password.', 'error')
            return render_template('signup.html', form=form)
        
        # Create user with email verification required
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role_id=3,  # Default to customer role
            email_verified=False,  # New users must verify email
            active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate and send OTP
        otp = EmailVerification.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        verification = EmailVerification(
            email=form.email.data,
            otp=otp,
            expires_at=expires_at
        )
        
        db.session.add(verification)
        db.session.commit()
        
        # Send email
        if send_email_otp(form.email.data, otp):
            flash('Account created successfully! Please check your email for verification code.', 'success')
            session['pending_verification_email'] = form.email.data
            return redirect(url_for('email_verification'))
        else:
            flash('Account created but email verification failed. Please contact support.', 'warning')
            return redirect(url_for('login'))
    
    return render_template('signup.html', form=form)

@app.route('/email-verification', methods=['GET', 'POST'])
def email_verification():
    """Email verification page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    pending_email = session.get('pending_verification_email')
    if not pending_email:
        flash('No pending verification found. Please sign up first.', 'error')
        return redirect(url_for('signup'))
    
    form = EmailVerificationForm()
    if form.validate_on_submit():
        # Verify OTP
        verification = EmailVerification.query.filter_by(
            email=pending_email,
            otp=form.otp.data,
            is_used=False
        ).first()
        
        if verification and not verification.is_expired():
            # Mark OTP as used
            verification.is_used = True
            
            # Mark user as verified
            user = User.query.filter_by(email=pending_email).first()
            if user:
                user.email_verified = True
                db.session.commit()
                
                # Clear session
                session.pop('pending_verification_email', None)
                
                flash('Email verified successfully! You can now login.', 'success')
                return redirect(url_for('login'))
        else:
            flash('Invalid or expired verification code. Please try again.', 'error')
    
    return render_template('email_verification.html', form=form)

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP for email verification"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    # Check if user exists and needs verification
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'No account found with this email'})
    
    if user.email_verified:
        return jsonify({'success': False, 'message': 'Email is already verified'})
    
    # Generate new OTP
    otp = EmailVerification.generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Invalidate old OTPs
    EmailVerification.query.filter_by(email=email, is_used=False).update({'is_used': True})
    
    verification = EmailVerification(
        email=email,
        otp=otp,
        expires_at=expires_at
    )
    
    db.session.add(verification)
    db.session.commit()
    
    # Send email
    if send_email_otp(email, otp):
        return jsonify({'success': True, 'message': 'Verification code sent successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send verification code'})

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = PasswordReset.generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Invalidate old tokens
            PasswordReset.query.filter_by(email=form.email.data, is_used=False).update({'is_used': True})
            
            reset_request = PasswordReset(
                email=form.email.data,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset_request)
            db.session.commit()
            
            # Send email
            if send_password_reset_email(form.email.data, token):
                flash('Password reset link has been sent to your email.', 'success')
            else:
                flash('Failed to send password reset email. Please try again.', 'error')
        else:
            flash('No account found with this email address.', 'error')
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    token = request.args.get('token')
    if not token:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('login'))
    
    # Verify token
    reset_request = PasswordReset.query.filter_by(
        token=token,
        is_used=False
    ).first()
    
    if not reset_request or reset_request.is_expired():
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Check password strength
        strength_check = check_password_strength(form.password.data)
        if strength_check['score'] < 3:
            flash('Password is too weak. Please choose a stronger password.', 'error')
            return render_template('reset_password.html', form=form)
        
        # Update user password
        user = User.query.filter_by(email=reset_request.email).first()
        if user:
            user.password_hash = generate_password_hash(form.password.data)
            reset_request.is_used = True
            db.session.commit()
            
            flash('Password has been reset successfully! You can now login with your new password.', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)

# Session Management Routes
@app.route('/sessions')
@login_required
def view_sessions():
    """View all active sessions for the current user"""
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    return render_template('sessions.html', sessions=sessions)

@app.route('/api/sessions')
@login_required
def get_sessions_api():
    """API endpoint to get user sessions"""
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            'id': session.id,
            'ip_address': session.ip_address,
            'device_info': session.device_info,
            'created_at': session.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_activity': session.last_activity.strftime('%Y-%m-%d %H:%M:%S'),
            'is_current': session.session_token == request.cookies.get('session_token', ''),
            'user_agent': session.user_agent[:100] + '...' if len(session.user_agent) > 100 else session.user_agent
        })
    
    return jsonify({'sessions': sessions_data})

@app.route('/api/sessions/<int:session_id>/terminate', methods=['POST'])
@login_required
def terminate_session(session_id):
    """Terminate a specific session"""
    session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()
    
    if not session:
        return jsonify({'success': False, 'message': 'Session not found'}), 404
    
    # Don't allow terminating current session
    if session.session_token == request.cookies.get('session_token', ''):
        return jsonify({'success': False, 'message': 'Cannot terminate current session'}), 400
    
    session.is_active = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Session terminated successfully'})

@app.route('/api/sessions/terminate-all', methods=['POST'])
@login_required
def terminate_all_sessions():
    """Terminate all sessions except current"""
    current_token = request.cookies.get('session_token', '')
    
    UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).filter(UserSession.session_token != current_token).update({'is_active': False})
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'All other sessions terminated successfully'})

@app.route('/api/sessions/terminate-current', methods=['POST'])
@login_required
def terminate_current_session():
    """Terminate current session (logout)"""
    current_token = request.cookies.get('session_token', '')
    
    if current_token:
        session = UserSession.query.filter_by(
            session_token=current_token,
            user_id=current_user.id
        ).first()
        
        if session:
            session.is_active = False
            db.session.commit()
    
    return jsonify({'success': True, 'message': 'Current session terminated'})
