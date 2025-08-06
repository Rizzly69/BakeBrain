#!/usr/bin/env python3
"""
Create sample data for the bakery management system
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_sample_data():
    """Create sample data for the application"""
    
    try:
        # Import after setting up the path
        from app import app
        from models import db, User, Product, Inventory, Order, OrderItem, Category, Role, AIInsight, OrderStatus, OrderType
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            print("Creating sample data...")
            
            # Check if we already have data
            if Order.query.count() > 0:
                print("Sample data already exists. Skipping...")
                return
            
            # Create categories
            categories_data = [
                ('Breads', 'Fresh baked breads and loaves'),
                ('Pastries', 'Sweet and savory pastries'),
                ('Cakes', 'Custom cakes and desserts'),
                ('Cookies', 'Cookies and biscuits'),
                ('Beverages', 'Coffee, tea, and other drinks')
            ]
            
            categories = {}
            for name, description in categories_data:
                category = Category(name=name, description=description)
                db.session.add(category)
                db.session.flush()  # Get the ID
                categories[name] = category.id
            
            db.session.commit()
            print("✓ Categories created")
            
            # Create products
            products_data = [
                ('Artisan Sourdough', 'Hand-crafted sourdough bread', 8.50, 'Breads', 'BREAD001'),
                ('Croissant', 'Buttery French croissant', 3.25, 'Pastries', 'PAST001'),
                ('Chocolate Cake', 'Rich chocolate layer cake', 25.00, 'Cakes', 'CAKE001'),
                ('Chocolate Chip Cookies', 'Classic chocolate chip cookies (dozen)', 12.00, 'Cookies', 'COOK001'),
                ('Fresh Coffee', 'Locally roasted coffee blend', 4.50, 'Beverages', 'BEV001'),
                ('Baguette', 'Traditional French baguette', 4.00, 'Breads', 'BREAD002'),
                ('Danish Pastry', 'Sweet Danish with fruit filling', 4.75, 'Pastries', 'PAST002'),
                ('Wedding Cake', 'Custom wedding cake (per tier)', 85.00, 'Cakes', 'CAKE002'),
            ]
            
            products = []
            for name, description, price, category_name, sku in products_data:
                product = Product(
                    name=name,
                    description=description,
                    price=price,
                    category_id=categories[category_name],
                    sku=sku
                )
                db.session.add(product)
                db.session.flush()  # Get the ID
                products.append(product)
            
            db.session.commit()
            print("✓ Products created")
            
            # Create inventory
            for product in products:
                inventory = Inventory(
                    product_id=product.id,
                    quantity=50,
                    min_stock_level=10,
                    max_stock_level=100,
                    last_updated=datetime.utcnow()
                )
                db.session.add(inventory)
            
            db.session.commit()
            print("✓ Inventory created")
            
            # Create customer user
            customer_role = Role.query.filter_by(name='customer').first()
            if not customer_role:
                customer_role = Role(name='customer', description='Customer with order access')
                db.session.add(customer_role)
                db.session.commit()
            
            customer = User.query.filter_by(username='customer1').first()
            if not customer:
                customer = User(
                    username='customer1',
                    email='customer1@bakery.com',
                    password_hash=generate_password_hash('customer123'),
                    first_name='John',
                    last_name='Doe',
                    role_id=customer_role.id
                )
                db.session.add(customer)
                db.session.commit()
            
            # Create sample orders
            order_statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION, OrderStatus.READY, OrderStatus.DELIVERED]
            
            for i in range(20):  # Create 20 sample orders
                order = Order(
                    order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    customer_id=customer.id,
                    order_type=OrderType.REGULAR,
                    status=order_statuses[i % len(order_statuses)],
                    total_amount=float(products[i % len(products)].price) * (i % 3 + 1),
                    created_at=datetime.now() - timedelta(days=i)
                )
                db.session.add(order)
                db.session.flush()  # Get the order ID
                
                # Add order items
                product = products[i % len(products)]
                quantity = i % 3 + 1
                unit_price = float(product.price)
                total_price = unit_price * quantity
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                db.session.add(order_item)
            
            db.session.commit()
            print("✓ Orders created")
            
            # Create AI insights
            insights_data = [
                ('Demand Forecast', 'Based on historical data, expect 20% increase in cake orders for the upcoming weekend.', 0.85),
                ('Inventory Alert', 'Croissant inventory is running low. Consider restocking within 2 days.', 0.92),
                ('Revenue Trend', 'Weekend sales show 15% higher revenue compared to weekdays.', 0.78),
                ('Customer Insights', 'Most popular product is Artisan Sourdough with 45% of total sales.', 0.88),
                ('Seasonal Trend', 'Cake orders increase by 30% during holiday seasons.', 0.82)
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
            print("✓ AI insights created")
            
            print("\n🎉 Sample data created successfully!")
            print(f"📊 {Order.query.count()} orders created")
            print(f"📦 {Product.query.count()} products created")
            print(f"🤖 {AIInsight.query.count()} AI insights created")
            print(f"👥 {User.query.count()} users created")
            print("\nYou can now access the application and see real data!")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_sample_data() 