
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Enum
import enum

# Create a new SQLAlchemy instance
db = SQLAlchemy()




class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    @staticmethod
    def create(user_id, message):
        from app import db
        notif = Notification(user_id=user_id, message=message)
        db.session.add(notif)
        db.session.commit()
        return notif

# Create a new SQLAlchemy instance
db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship('User', backref='role', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
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
    staff_schedules = db.relationship('StaffSchedule', backref='staff_member', lazy=True, foreign_keys='StaffSchedule.staff_id')
    schedule_modifications = db.relationship('ScheduleModification', backref='modifier_user', lazy=True, foreign_keys='ScheduleModification.modified_by', overlaps="modifier_user,schedule_modifications_tracked,schedule_modifications_made,modifier")


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    __tablename__ = 'product'
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


class RawProduct(db.Model):
    __tablename__ = 'raw_product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    unit_of_measure = db.Column(db.String(32), nullable=False, default='units')  # kg, liters, pieces, etc.
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    supplier = db.Column(db.String(128))
    supplier_contact = db.Column(db.String(128))
    location = db.Column(db.String(128), default='Storage')  # Storage location
    current_stock = db.Column(db.Numeric(10, 3), nullable=False, default=0)  # Allow decimal for precise measurements
    min_stock_level = db.Column(db.Numeric(10, 3), default=10)
    reorder_point = db.Column(db.Numeric(10, 3), default=5)
    expiry_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_restocked = db.Column(db.DateTime)
    
    def is_low_stock(self):
        return self.current_stock <= self.min_stock_level
    
    def is_critical_stock(self):
        return self.current_stock <= self.reorder_point


class Inventory(db.Model):
    __tablename__ = 'inventory'
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
    __tablename__ = 'order'
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
    __tablename__ = 'order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    special_instructions = db.Column(db.Text)


class StaffSchedule(db.Model):
    __tablename__ = 'staff_schedule'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    position = db.Column(db.String(64))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_modified = db.Column(db.Boolean, default=False)
    modification_reason = db.Column(db.Text)
    modified_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    original_schedule_id = db.Column(db.Integer, db.ForeignKey('staff_schedule.id'))
    
    # Relationships
    modifier = db.relationship('User', foreign_keys=[modified_by], backref='schedule_modifications_made')
    original_schedule = db.relationship('StaffSchedule', remote_side=[id], backref='modifications', foreign_keys=[original_schedule_id])


class ScheduleModification(db.Model):
    __tablename__ = 'schedule_modification'
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('staff_schedule.id'), nullable=False)
    modification_type = db.Column(db.String(32), nullable=False)  # 'created', 'updated', 'deleted'
    old_start_time = db.Column(db.Time)
    old_end_time = db.Column(db.Time)
    old_position = db.Column(db.String(64))
    old_notes = db.Column(db.Text)
    new_start_time = db.Column(db.Time)
    new_end_time = db.Column(db.Time)
    new_position = db.Column(db.String(64))
    new_notes = db.Column(db.Text)
    reason = db.Column(db.Text)
    modified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    schedule = db.relationship('StaffSchedule', backref='modification_history')
    modifier = db.relationship('User', backref=db.backref('schedule_modifications_tracked', overlaps="modifier_user"), foreign_keys=[modified_by], overlaps="modifier_user,schedule_modifications,schedule_modifications_made")


class AIInsight(db.Model):
    __tablename__ = 'ai_insight'
    id = db.Column(db.Integer, primary_key=True)
    insight_type = db.Column(db.String(64), nullable=False)  # demand_forecast, inventory_optimization, etc.
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float)
    data = db.Column(db.JSON)  # Additional structured data
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Configuration(db.Model):
    __tablename__ = 'configuration'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(64), nullable=False)  # company, invoice, system, etc.
    data_type = db.Column(db.String(32), default='string')  # string, integer, float, boolean, json
    is_editable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_value(cls, key, default=None):
        """Get configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        if config:
            return config.get_typed_value()
        return default
    
    @classmethod
    def set_value(cls, key, value, description=None, category='system', data_type='string'):
        """Set configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = str(value)
            config.description = description or config.description
            config.category = category
            config.data_type = data_type
            config.updated_at = datetime.utcnow()
        else:
            config = cls(
                key=key,
                value=str(value),
                description=description,
                category=category,
                data_type=data_type
            )
            db.session.add(config)
        db.session.commit()
        return config
    
    def get_typed_value(self):
        """Get value with proper type conversion"""
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value
