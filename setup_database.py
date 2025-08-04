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
            ('admin', 'admin@bakery.com', 'admin123', admin_role.id),
            ('manager1', 'manager1@bakery.com', 'manager123', manager_role.id),
            ('staff1', 'staff1@bakery.com', 'staff123', staff_role.id),
            ('customer1', 'customer1@bakery.com', 'customer123', customer_role.id),
            ('baker1', 'baker1@bakery.com', 'baker123', baker_role.id)
        ]
        
        for username, email, password, role_id in users_data:
            if not User.query.filter_by(username=username).first():
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password),
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
        
        print("Database setup completed successfully!")
        print("\nTest accounts created:")
        print("- Admin: admin / admin123")
        print("- Manager: manager1 / manager123")
        print("- Staff: staff1 / staff123")
        print("- Customer: customer1 / customer123")
        print("- Baker: baker1 / baker123")
        print("\nYou can now run the application with: python main.py")

if __name__ == '__main__':
    setup_database()