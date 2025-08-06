#!/usr/bin/env python3
"""
Quick setup script to add sample data to the database
"""

import sqlite3
from datetime import datetime, timedelta
import os

def add_sample_data():
    """Add sample data directly to SQLite database"""
    
    db_path = 'bakery.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("Database file not found. Please run the application first to create it.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM 'order'")
        order_count = cursor.fetchone()[0]
        
        if order_count > 0:
            print(f"Database already has {order_count} orders. Skipping sample data creation.")
            return
        
        print("Adding sample data to database...")
        
        # Get customer ID
        cursor.execute("SELECT id FROM user WHERE username = 'customer1'")
        customer_result = cursor.fetchone()
        
        if not customer_result:
            print("Customer1 not found. Creating sample user...")
            # Create customer role if not exists
            cursor.execute("INSERT OR IGNORE INTO role (name, description) VALUES (?, ?)", 
                         ('customer', 'Customer with order access'))
            conn.commit()
            
            # Get customer role ID
            cursor.execute("SELECT id FROM role WHERE name = 'customer'")
            customer_role_id = cursor.fetchone()[0]
            
            # Create customer user
            cursor.execute("""
                INSERT INTO user (username, email, password_hash, first_name, last_name, role_id, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ('customer1', 'customer1@bakery.com', 
                  'pbkdf2:sha256:600000$hash$password', 'John', 'Doe', customer_role_id, 1, datetime.now()))
            conn.commit()
            
            customer_id = cursor.lastrowid
        else:
            customer_id = customer_result[0]
        
        # Get product IDs
        cursor.execute("SELECT id FROM product LIMIT 5")
        products = cursor.fetchall()
        
        if not products:
            print("No products found. Creating sample products...")
            # Create categories
            categories = [
                ('Breads', 'Fresh baked breads and loaves'),
                ('Pastries', 'Sweet and savory pastries'),
                ('Cakes', 'Custom cakes and desserts'),
                ('Cookies', 'Cookies and biscuits'),
                ('Beverages', 'Coffee, tea, and other drinks')
            ]
            
            for name, description in categories:
                cursor.execute("INSERT INTO category (name, description, is_active) VALUES (?, ?, ?)",
                             (name, description, 1))
            conn.commit()
            
            # Create products
            products_data = [
                ('Artisan Sourdough', 'Hand-crafted sourdough bread', 8.50, 1, 'BREAD001'),
                ('Croissant', 'Buttery French croissant', 3.25, 2, 'PAST001'),
                ('Chocolate Cake', 'Rich chocolate layer cake', 25.00, 3, 'CAKE001'),
                ('Chocolate Chip Cookies', 'Classic chocolate chip cookies (dozen)', 12.00, 4, 'COOK001'),
                ('Fresh Coffee', 'Locally roasted coffee blend', 4.50, 5, 'BEV001'),
            ]
            
            for name, description, price, category_id, sku in products_data:
                cursor.execute("""
                    INSERT INTO product (name, description, price, category_id, sku, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, description, price, category_id, sku, 1, datetime.now()))
            conn.commit()
            
            # Get product IDs
            cursor.execute("SELECT id FROM product LIMIT 5")
            products = cursor.fetchall()
        
        # Create sample orders
        print("Creating sample orders...")
        order_statuses = ['pending', 'confirmed', 'in_preparation', 'ready', 'delivered']
        
        for i in range(15):
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}"
            status = order_statuses[i % len(order_statuses)]
            total_amount = float(products[i % len(products)][0]) * (i % 3 + 1)
            created_at = datetime.now() - timedelta(days=i)
            
            cursor.execute("""
                INSERT INTO 'order' (order_number, customer_id, order_type, status, total_amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_number, customer_id, 'regular', status, total_amount, created_at, created_at))
            
            order_id = cursor.lastrowid
            
            # Add order items
            product_id = products[i % len(products)][0]
            quantity = i % 3 + 1
            unit_price = float(products[i % len(products)][0])
            total_price = unit_price * quantity
            
            cursor.execute("""
                INSERT INTO order_item (order_id, product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, product_id, quantity, unit_price, total_price))
        
        conn.commit()
        
        # Create AI insights
        print("Creating AI insights...")
        insights_data = [
            ('demand_forecast', 'Demand Forecast', 'Based on historical data, expect 20% increase in cake orders for the upcoming weekend.', 0.85),
            ('inventory_optimization', 'Inventory Alert', 'Croissant inventory is running low. Consider restocking within 2 days.', 0.92),
            ('revenue_analysis', 'Revenue Trend', 'Weekend sales show 15% higher revenue compared to weekdays.', 0.78)
        ]
        
        for insight_type, title, description, confidence in insights_data:
            cursor.execute("""
                INSERT INTO ai_insight (insight_type, title, description, confidence_score, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (insight_type, title, description, confidence, 1, datetime.now()))
        
        conn.commit()
        
        print("Sample data created successfully!")
        print(f"- 15 sample orders created")
        print(f"- 3 AI insights created")
        print("\nYou can now access the application and see real data in the dashboard!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_sample_data() 