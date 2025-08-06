#!/usr/bin/env python3
"""
Add sample data using Flask app context
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_sample_data():
    """Add sample data using Flask app context"""
    
    try:
        from app import app, db
        from models import User, Product, Inventory, Order, OrderItem, Category, Role, AIInsight, OrderStatus, OrderType
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            print("Adding sample data to database...")
            
            # Check if we already have orders
            existing_orders = Order.query.count()
            if existing_orders > 0:
                print(f"Database already has {existing_orders} orders. Skipping sample data creation.")
                return
            
            # Create roles if they don't exist
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
            users_data = [
                ('admin', 'admin@bakery.com', 'admin123', 'Admin', 'User', 'admin'),
                ('manager1', 'manager1@bakery.com', 'manager123', 'Manager', 'User', 'manager'),
                ('staff1', 'staff1@bakery.com', 'staff123', 'Staff', 'User', 'staff'),
                ('customer1', 'customer1@bakery.com', 'customer123', 'John', 'Doe', 'customer'),
                ('baker1', 'baker1@bakery.com', 'baker123', 'Baker', 'User', 'baker')
            ]
            
            for username, email, password, first_name, last_name, role_name in users_data:
                if not User.query.filter_by(username=username).first():
                    role = Role.query.filter_by(name=role_name).first()
                    user = User(
                        username=username,
                        email=email,
                        password_hash=generate_password_hash(password),
                        first_name=first_name,
                        last_name=last_name,
                        role_id=role.id
                    )
                    db.session.add(user)
            db.session.commit()
            
            # Create categories
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
            products_data = [
                ('Artisan Sourdough', 'Hand-crafted sourdough bread', 8.50, 'Breads', 'BREAD001'),
                ('Croissant', 'Buttery French croissant', 3.25, 'Pastries', 'PAST001'),
                ('Chocolate Cake', 'Rich chocolate layer cake', 25.00, 'Cakes', 'CAKE001'),
                ('Chocolate Chip Cookies', 'Classic chocolate chip cookies (dozen)', 12.00, 'Cookies', 'COOK001'),
                ('Fresh Coffee', 'Locally roasted coffee blend', 4.50, 'Beverages', 'BEV001'),
            ]
            
            for name, description, price, category_name, sku in products_data:
                if not Product.query.filter_by(sku=sku).first():
                    category = Category.query.filter_by(name=category_name).first()
                    product = Product(
                        name=name,
                        description=description,
                        price=price,
                        category_id=category.id,
                        sku=sku
                    )
                    db.session.add(product)
            db.session.commit()
            
            # Create inventory
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
            customer1 = User.query.filter_by(username='customer1').first()
            products = Product.query.all()
            order_statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION, OrderStatus.READY, OrderStatus.DELIVERED]
            
            for i in range(15):
                order = Order(
                    order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    customer_id=customer1.id,
                    order_type=OrderType.REGULAR,
                    status=order_statuses[i % len(order_statuses)],
                    total_amount=float(products[i % len(products)].price) * (i % 3 + 1),
                    created_at=datetime.now() - timedelta(days=i)
                )
                db.session.add(order)
                
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
            
            # Create AI insights
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
            
            print("Sample data created successfully!")
            print(f"- {Order.query.count()} orders created")
            print(f"- {AIInsight.query.count()} AI insights created")
            print("\nYou can now access the application and see real data in the dashboard!")
            
    except Exception as e:
        print(f"Error creating sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_sample_data() 