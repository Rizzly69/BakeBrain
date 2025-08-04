from datetime import datetime, date
from app import db
from flask_login import UserMixin
from sqlalchemy import Enum
import enum


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship('User', backref='role', lazy=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_active(self):
        return self.active
        
    @is_active.setter
    def is_active(self, value):
        self.active = value
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True, foreign_keys='Order.customer_id')
    staff_schedules = db.relationship('StaffSchedule', backref='staff_member', lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2))
    sku = db.Column(db.String(64), unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    requires_preparation = db.Column(db.Boolean, default=False)
    preparation_time = db.Column(db.Integer)  # in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    inventory_items = db.relationship('Inventory', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    max_stock_level = db.Column(db.Integer, default=100)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_restocked = db.Column(db.DateTime)
    
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level


class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PREPARATION = "in_preparation"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderType(enum.Enum):
    REGULAR = "regular"
    CATERING = "catering"
    ONLINE = "online"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(32), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_type = db.Column(Enum(OrderType), default=OrderType.REGULAR)
    status = db.Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    delivery_date = db.Column(db.DateTime)
    delivery_address = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Catering specific fields
    event_date = db.Column(db.DateTime)
    guest_count = db.Column(db.Integer)
    setup_requirements = db.Column(db.Text)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    special_instructions = db.Column(db.Text)


class StaffSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    position = db.Column(db.String(64))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AIInsight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insight_type = db.Column(db.String(64), nullable=False)  # demand_forecast, inventory_optimization, etc.
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float)
    data = db.Column(db.JSON)  # Additional structured data
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
