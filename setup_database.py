#!/usr/bin/env python3
"""
Database setup script for Smart Bakery Management System
Run this script to initialize the database with sample data
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import *
from werkzeug.security import generate_password_hash

def setup_database():
    """Initialize database with tables and sample data"""
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Create roles
        print("Creating roles...")
        roles_data = [
            ('admin', 'Administrator with full access'),
            ('manager', 'Manager with operational access'),
            ('staff', 'Staff with limited access'),
            ('customer', 'Customer with order access'),
            ('baker', 'Baker with production access')
        ]
        
        for role_name, description in roles_data:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name, description=description)
                db.session.add(role)
        
        db.session.commit()
        
        # Create test users
        print("Creating test users...")
        admin_role = Role.query.filter_by(name='admin').first()
        manager_role = Role.query.filter_by(name='manager').first()
        staff_role = Role.query.filter_by(name='staff').first()
        customer_role = Role.query.filter_by(name='customer').first()
        baker_role = Role.query.filter_by(name='baker').first()
        
        users_data = [
            ('admin', 'admin@bakery.com', 'admin123', 'Admin', 'User', admin_role.id),
            ('manager1', 'manager1@bakery.com', 'manager123', 'Manager', 'One', manager_role.id),
            ('staff1', 'staff1@bakery.com', 'staff123', 'Staff', 'One', staff_role.id),
            ('customer1', 'customer1@bakery.com', 'customer123', 'Customer', 'One', customer_role.id),
            ('baker1', 'baker1@bakery.com', 'baker123', 'Baker', 'One', baker_role.id)
        ]
        
        for username, email, password, first_name, last_name, role_id in users_data:
            if not User.query.filter_by(username=username).first():
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password),
                    first_name=first_name,
                    last_name=last_name,
                    role_id=role_id
                )
                db.session.add(user)
        
        db.session.commit()
        
        # Create categories
        print("Creating product categories...")
        categories_data = [
            ('Breads', 'Fresh baked breads and loaves'),
            ('Pastries', 'Sweet and savory pastries'),
            ('Cakes', 'Custom cakes and desserts'),
            ('Cookies', 'Cookies and biscuits'),
            ('Beverages', 'Coffee, tea, and other drinks')
        ]
        
        for name, description in categories_data:
            if not Category.query.filter_by(name=name).first():
                category = Category(name=name, description=description)
                db.session.add(category)
        
        db.session.commit()
        
        # Create products
        print("Creating products...")
        bread_cat = Category.query.filter_by(name='Breads').first()
        pastry_cat = Category.query.filter_by(name='Pastries').first()
        cake_cat = Category.query.filter_by(name='Cakes').first()
        cookie_cat = Category.query.filter_by(name='Cookies').first()
        beverage_cat = Category.query.filter_by(name='Beverages').first()
        
        products_data = [
            ('Artisan Sourdough', 'Hand-crafted sourdough bread', 8.50, bread_cat.id, 'BREAD001'),
            ('Croissant', 'Buttery French croissant', 3.25, pastry_cat.id, 'PAST001'),
            ('Chocolate Cake', 'Rich chocolate layer cake', 25.00, cake_cat.id, 'CAKE001'),
            ('Chocolate Chip Cookies', 'Classic chocolate chip cookies (dozen)', 12.00, cookie_cat.id, 'COOK001'),
            ('Fresh Coffee', 'Locally roasted coffee blend', 4.50, beverage_cat.id, 'BEV001'),
            ('Baguette', 'Traditional French baguette', 4.00, bread_cat.id, 'BREAD002'),
            ('Danish Pastry', 'Sweet Danish with fruit filling', 4.75, pastry_cat.id, 'PAST002'),
            ('Wedding Cake', 'Custom wedding cake (per tier)', 85.00, cake_cat.id, 'CAKE002'),
        ]
        
        for name, description, price, category_id, sku in products_data:
            if not Product.query.filter_by(sku=sku).first():
                product = Product(
                    name=name,
                    description=description,
                    price=price,
                    category_id=category_id,
                    sku=sku
                )
                db.session.add(product)
        
        db.session.commit()
        
        # Create inventory
        print("Creating inventory...")
        products = Product.query.all()
        for product in products:
            if not Inventory.query.filter_by(product_id=product.id).first():
                inventory = Inventory(
                    product_id=product.id,
                    quantity=50,
                    min_stock_level=10,
                    max_stock_level=100,
                    last_updated=datetime.utcnow()
                )
                db.session.add(inventory)
        
        db.session.commit()
        
        # Create sample orders
        print("Creating sample orders...")
        customer1 = User.query.filter_by(username='customer1').first()
        products = Product.query.all()
        
        if customer1 and products:
            # Create some sample orders with different statuses
            order_statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION, OrderStatus.READY, OrderStatus.DELIVERED]
            
            for i in range(15):  # Create 15 sample orders
                order = Order(
                    order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    customer_id=customer1.id,
                    order_type=OrderType.REGULAR,
                    status=order_statuses[i % len(order_statuses)],
                    total_amount=float(products[i % len(products)].price) * (i % 3 + 1),
                    created_at=datetime.now() - timedelta(days=i)
                )
                db.session.add(order)
                db.session.flush()  # Flush to get the order ID
                
                # Add order items
                product = products[i % len(products)]
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=i % 3 + 1,
                    unit_price=float(product.price),
                    total_price=float(product.price) * (i % 3 + 1)
                )
                db.session.add(order_item)
        
        db.session.commit()
        
        # Create raw products
        print("Creating raw products...")
        raw_products_data = [
            ('All-Purpose Flour', 'High-quality all-purpose flour for baking', 'kg', 2.50, 'Local Flour Mill', '555-0101', 'Storage A', 50.0, 10.0, 5.0),
            ('Sugar', 'Granulated white sugar', 'kg', 1.80, 'Sweet Suppliers Inc', '555-0102', 'Storage A', 30.0, 8.0, 3.0),
            ('Butter', 'Unsalted butter for baking', 'kg', 8.00, 'Dairy Delights', '555-0103', 'Refrigerator', 15.0, 5.0, 2.0),
            ('Eggs', 'Fresh farm eggs', 'pieces', 0.30, 'Fresh Farm Eggs', '555-0104', 'Refrigerator', 200.0, 50.0, 20.0),
            ('Milk', 'Whole milk for recipes', 'l', 2.20, 'Dairy Delights', '555-0103', 'Refrigerator', 20.0, 5.0, 2.0),
            ('Vanilla Extract', 'Pure vanilla extract', 'ml', 0.05, 'Flavor Masters', '555-0105', 'Storage B', 1000.0, 200.0, 100.0),
            ('Chocolate Chips', 'Semi-sweet chocolate chips', 'kg', 12.00, 'Chocolate World', '555-0106', 'Storage B', 8.0, 3.0, 1.0),
            ('Yeast', 'Active dry yeast', 'g', 0.02, 'Baking Essentials', '555-0107', 'Storage A', 500.0, 100.0, 50.0),
            ('Salt', 'Fine sea salt', 'kg', 1.50, 'Salt Suppliers', '555-0108', 'Storage A', 25.0, 5.0, 2.0),
            ('Olive Oil', 'Extra virgin olive oil', 'l', 15.00, 'Oil Importers', '555-0109', 'Storage B', 10.0, 3.0, 1.0)
        ]
        
        for name, description, unit, cost, supplier, contact, location, stock, min_level, reorder in raw_products_data:
            if not RawProduct.query.filter_by(name=name).first():
                raw_product = RawProduct(
                    name=name,
                    description=description,
                    unit_of_measure=unit,
                    cost_per_unit=cost,
                    supplier=supplier,
                    supplier_contact=contact,
                    location=location,
                    current_stock=stock,
                    min_stock_level=min_level,
                    reorder_point=reorder
                )
                db.session.add(raw_product)
        
        db.session.commit()
        
        # Create product recipes
        print("Creating product recipes...")
        recipes_data = [
            ('Artisan Sourdough', 'All-Purpose Flour', 0.5, 'kg'),
            ('Artisan Sourdough', 'Water', 0.3, 'l'),
            ('Artisan Sourdough', 'Salt', 0.01, 'kg'),
            ('Artisan Sourdough', 'Yeast', 0.005, 'kg'),
            ('Croissant', 'All-Purpose Flour', 0.25, 'kg'),
            ('Croissant', 'Butter', 0.15, 'kg'),
            ('Croissant', 'Yeast', 0.01, 'kg'),
            ('Croissant', 'Salt', 0.005, 'kg'),
            ('Chocolate Cake', 'All-Purpose Flour', 0.3, 'kg'),
            ('Chocolate Cake', 'Sugar', 0.4, 'kg'),
            ('Chocolate Cake', 'Eggs', 4, 'pieces'),
            ('Chocolate Cake', 'Milk', 0.25, 'l'),
            ('Chocolate Cake', 'Chocolate Chips', 0.2, 'kg'),
            ('Chocolate Chip Cookies', 'All-Purpose Flour', 0.15, 'kg'),
            ('Chocolate Chip Cookies', 'Butter', 0.1, 'kg'),
            ('Chocolate Chip Cookies', 'Sugar', 0.12, 'kg'),
            ('Chocolate Chip Cookies', 'Eggs', 1, 'pieces'),
            ('Chocolate Chip Cookies', 'Chocolate Chips', 0.15, 'kg')
        ]
        
        for product_name, raw_product_name, quantity, unit in recipes_data:
            product = Product.query.filter_by(name=product_name).first()
            raw_product = RawProduct.query.filter_by(name=raw_product_name).first()
            
            if product and raw_product:
                # Check if recipe already exists
                existing_recipe = ProductRecipe.query.filter_by(
                    product_id=product.id,
                    raw_product_id=raw_product.id
                ).first()
                
                if not existing_recipe:
                    recipe = ProductRecipe(
                        product_id=product.id,
                        raw_product_id=raw_product.id,
                        quantity_required=quantity,
                        unit_of_measure=unit
                    )
                    db.session.add(recipe)
        
        db.session.commit()
        
        # Create AI insights
        print("Creating AI insights...")
        insights_data = [
            ('Demand Forecast', 'Based on historical data, expect 20% increase in cake orders for the upcoming weekend.', 0.85),
            ('Inventory Alert', 'Croissant inventory is running low. Consider restocking within 2 days.', 0.92),
            ('Revenue Trend', 'Weekend sales show 15% higher revenue compared to weekdays.', 0.78)
        ]
        
        for title, description, confidence in insights_data:
            insight = AIInsight(
                insight_type='demand_forecast',
                title=title,
                description=description,
                confidence_score=confidence
            )
            db.session.add(insight)
        
        db.session.commit()
        
        print("Database setup completed successfully!")
        print("\nTest accounts created:")
        print("- Admin: admin / admin123")
        print("- Manager: manager1 / manager123")
        print("- Staff: staff1 / staff123")
        print("- Customer: customer1 / customer123")
        print("- Baker: baker1 / baker123")
        print("\nSample data created:")
        print("- 15 sample orders with various statuses")
        print("- AI insights for business intelligence")
        print("\nYou can now run the application with: python main.py")

def initialize_configuration():
    """Initialize default configuration values"""
    from models import Configuration, db
    
    # Company Information
    default_configs = [
        # Company Details
        ('company_name', 'Smart Bakery Manager', 'Company name displayed on invoices and reports', 'company', 'string'),
        ('company_tagline', 'Premium Artisan Bakery', 'Company tagline or subtitle', 'company', 'string'),
        ('company_address', '123 Baker Street, Bakery District', 'Company address', 'company', 'text'),
        ('company_phone', '(555) 123-BAKE', 'Company phone number', 'company', 'string'),
        ('company_email', 'orders@smartbakery.com', 'Company email address', 'company', 'string'),
        ('company_website', 'www.smartbakery.com', 'Company website', 'company', 'string'),
        
        # Invoice Settings
        ('invoice_prefix', 'INV', 'Prefix for invoice numbers', 'invoice', 'string'),
        ('invoice_start_number', '1000', 'Starting invoice number', 'invoice', 'integer'),
        ('tax_rate', '8.5', 'Default tax rate percentage', 'invoice', 'float'),
        ('currency_symbol', '$', 'Currency symbol for invoices', 'invoice', 'string'),
        ('invoice_terms', 'Payment due within 30 days', 'Default payment terms', 'invoice', 'text'),
        ('invoice_footer', 'Thank you for choosing Smart Bakery Manager!', 'Invoice footer message', 'invoice', 'text'),
        
        # System Settings
        ('default_order_status', 'PENDING', 'Default status for new orders', 'system', 'string'),
        ('auto_generate_order_numbers', 'true', 'Automatically generate order numbers', 'system', 'boolean'),
        ('order_number_prefix', 'ORD', 'Prefix for order numbers', 'system', 'string'),
        ('order_number_start', '1000', 'Starting order number', 'system', 'integer'),
        ('enable_ai_insights', 'true', 'Enable AI insights generation', 'system', 'boolean'),
        ('ai_insight_frequency', '24', 'AI insights generation frequency in hours', 'system', 'integer'),
        
        # Inventory Settings
        ('default_min_stock', '10', 'Default minimum stock level', 'inventory', 'integer'),
        ('default_max_stock', '100', 'Default maximum stock level', 'inventory', 'integer'),
        ('low_stock_threshold', '5', 'Threshold for low stock alerts', 'inventory', 'integer'),
        ('enable_stock_alerts', 'true', 'Enable low stock alerts', 'inventory', 'boolean'),
        
        # Delivery Settings
        ('delivery_fee', '5.00', 'Default delivery fee', 'delivery', 'float'),
        ('free_delivery_threshold', '50.00', 'Minimum order amount for free delivery', 'delivery', 'float'),
        ('delivery_time_slots', '["9:00 AM", "12:00 PM", "3:00 PM", "6:00 PM"]', 'Available delivery time slots', 'delivery', 'json'),
        ('max_delivery_distance', '25', 'Maximum delivery distance in miles', 'delivery', 'integer'),
        
        # Catering Settings
        ('catering_deposit_percentage', '25', 'Required deposit percentage for catering orders', 'catering', 'integer'),
        ('catering_advance_notice', '72', 'Minimum advance notice for catering orders in hours', 'catering', 'integer'),
        ('catering_min_guest_count', '10', 'Minimum guest count for catering orders', 'catering', 'integer'),
        ('catering_setup_fee', '25.00', 'Default setup fee for catering orders', 'catering', 'float'),
        
        # Notification Settings
        ('email_notifications', 'true', 'Enable email notifications', 'notifications', 'boolean'),
        ('sms_notifications', 'false', 'Enable SMS notifications', 'notifications', 'boolean'),
        ('order_confirmation_email', 'true', 'Send order confirmation emails', 'notifications', 'boolean'),
        ('delivery_reminder_email', 'true', 'Send delivery reminder emails', 'notifications', 'boolean'),
        
        # Report Settings
        ('report_logo_enabled', 'true', 'Include logo in reports', 'reports', 'boolean'),
        ('report_footer_text', 'Generated by Smart Bakery Manager', 'Footer text for reports', 'reports', 'text'),
        ('daily_report_recipients', '["manager@smartbakery.com"]', 'Email addresses for daily reports', 'reports', 'json'),
        ('auto_generate_reports', 'true', 'Automatically generate daily reports', 'reports', 'boolean'),
    ]
    
    for key, value, description, category, data_type in default_configs:
        existing = Configuration.query.filter_by(key=key).first()
        if not existing:
            config = Configuration(
                key=key,
                value=value,
                description=description,
                category=category,
                data_type=data_type
            )
            db.session.add(config)
    
    db.session.commit()
    print("Configuration initialized successfully!")


if __name__ == '__main__':
    with app.app_context():
        setup_database()
        initialize_configuration()
        print("Database setup completed!")