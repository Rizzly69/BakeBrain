#!/usr/bin/env python3
"""
Add sample data to the database
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import *
from werkzeug.security import generate_password_hash

def add_sample_data():
    """Add sample orders and data to the database"""
    
    with app.app_context():
        print("Adding sample data...")
        
        # Check if we already have orders
        existing_orders = Order.query.count()
        if existing_orders > 0:
            print(f"Database already has {existing_orders} orders. Skipping sample data creation.")
            return
        
        # Get customer and products
        customer1 = User.query.filter_by(username='customer1').first()
        products = Product.query.all()
        
        if not customer1:
            print("Customer1 not found. Creating sample user...")
            customer_role = Role.query.filter_by(name='customer').first()
            if customer_role:
                customer1 = User(
                    username='customer1',
                    email='customer1@bakery.com',
                    password_hash=generate_password_hash('customer123'),
                    first_name='John',
                    last_name='Doe',
                    role_id=customer_role.id
                )
                db.session.add(customer1)
                db.session.commit()
        
        if not products:
            print("No products found. Creating sample products...")
            # Create categories first
            categories_data = [
                ('Breads', 'Fresh baked breads and loaves'),
                ('Pastries', 'Sweet and savory pastries'),
                ('Cakes', 'Custom cakes and desserts'),
                ('Cookies', 'Cookies and biscuits'),
                ('Beverages', 'Coffee, tea, and other drinks')
            ]
            
            for name, description in categories_data:
                category = Category(name=name, description=description)
                db.session.add(category)
            db.session.commit()
            
            # Create products
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
            ]
            
            for name, description, price, category_id, sku in products_data:
                product = Product(
                    name=name,
                    description=description,
                    price=price,
                    category_id=category_id,
                    sku=sku
                )
                db.session.add(product)
            db.session.commit()
            products = Product.query.all()
        
        # Create sample orders
        print("Creating sample orders...")
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
        
        print("Sample data created successfully!")
        print(f"- {Order.query.count()} orders created")
        print(f"- {AIInsight.query.count()} AI insights created")

if __name__ == '__main__':
    add_sample_data() 