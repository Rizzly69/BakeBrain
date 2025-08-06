
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Enum
import enum
import secrets
import string

# Create a new SQLAlchemy instance
db = SQLAlchemy()

class EmailVerification(db.Model):
    __tablename__ = 'email_verification'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_otp():
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

class PasswordReset(db.Model):
    __tablename__ = 'password_reset'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at


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
    email_verified = db.Column(db.Boolean, default=False)
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


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)


class ProductRecipe(db.Model):
    __tablename__ = 'product_recipe'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    raw_product_id = db.Column(db.Integer, db.ForeignKey('raw_product.id'), nullable=False)
    quantity_required = db.Column(db.Numeric(10, 3), nullable=False)  # Amount of raw product needed per product unit
    unit_of_measure = db.Column(db.String(32), nullable=False)  # Unit for the recipe (e.g., grams, pieces)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='recipes')
    raw_product = db.relationship('RawProduct', backref='used_in_recipes')

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_order'
    
    id = db.Column(db.Integer, primary_key=True)
    raw_product_id = db.Column(db.Integer, db.ForeignKey('raw_product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    supplier_contact = db.Column(db.String(100), nullable=False)
    ordered_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, delivered, cancelled
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    raw_product = db.relationship('RawProduct', backref='purchase_orders')
    ordered_by_user = db.relationship('User', backref='purchase_orders')
    
    def __repr__(self):
        return f'<ProductRecipe {self.product.name} -> {self.raw_product.name}: {self.quantity_required} {self.unit_of_measure}>'


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
    
    def get_available_quantity(self):
        """Get the current available quantity in inventory"""
        inventory = Inventory.query.filter_by(product_id=self.id).first()
        return inventory.quantity if inventory else 0
    
    def get_max_orderable_quantity(self):
        """Get the maximum quantity that can be ordered based on inventory and raw materials"""
        available_inventory = self.get_available_quantity()
        
        # If there's sufficient inventory, return that
        if available_inventory > 0:
            return available_inventory
        
        # If no inventory but has recipe, calculate based on raw materials
        if self.recipes:
            max_from_raw_materials = float('inf')
            for recipe in self.recipes:
                if recipe.raw_product.current_stock > 0:
                    # Calculate how many products can be made from this raw material
                    possible_quantity = int(recipe.raw_product.current_stock / recipe.quantity_required)
                    max_from_raw_materials = min(max_from_raw_materials, possible_quantity)
                else:
                    max_from_raw_materials = 0
                    break
            
            return max_from_raw_materials if max_from_raw_materials != float('inf') else 0
        
        return 0
    
    def can_make_quantity(self, quantity):
        """Check if we can make the specified quantity based on raw materials"""
        if not self.recipes:
            return self.get_available_quantity() >= quantity
        
        for recipe in self.recipes:
            required_raw_quantity = recipe.quantity_required * quantity
            if recipe.raw_product.current_stock < required_raw_quantity:
                return False
        return True
    
    def consume_raw_materials(self, quantity):
        """Consume raw materials for the specified product quantity"""
        if not self.recipes:
            return True
        
        try:
            for recipe in self.recipes:
                required_raw_quantity = recipe.quantity_required * quantity
                if recipe.raw_product.current_stock < required_raw_quantity:
                    return False
                
                # Reduce raw material stock
                recipe.raw_product.current_stock -= required_raw_quantity
                recipe.raw_product.last_updated = datetime.utcnow()
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
    
    def restore_raw_materials(self, quantity):
        """Restore raw materials for the specified product quantity (used when order is cancelled)"""
        if not self.recipes:
            return True
        
        try:
            for recipe in self.recipes:
                required_raw_quantity = recipe.quantity_required * quantity
                
                # Restore raw material stock
                recipe.raw_product.current_stock += required_raw_quantity
                recipe.raw_product.last_updated = datetime.utcnow()
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


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
    
    def is_expiring_soon(self, days_threshold=7):
        """Check if the product is expiring within the specified days"""
        if not self.expiry_date:
            return False
        days_until_expiry = (self.expiry_date - date.today()).days
        return 0 <= days_until_expiry <= days_threshold
    
    def is_expired(self):
        """Check if the product has expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()
    
    def get_expiry_status(self):
        """Get expiry status with details"""
        if not self.expiry_date:
            return {'status': 'no_expiry', 'message': 'No expiry date set'}
        
        days_until_expiry = (self.expiry_date - date.today()).days
        
        if days_until_expiry < 0:
            return {'status': 'expired', 'message': f'Expired {abs(days_until_expiry)} days ago', 'days': days_until_expiry}
        elif days_until_expiry == 0:
            return {'status': 'expires_today', 'message': 'Expires today', 'days': days_until_expiry}
        elif days_until_expiry <= 3:
            return {'status': 'expires_soon', 'message': f'Expires in {days_until_expiry} days', 'days': days_until_expiry}
        elif days_until_expiry <= 7:
            return {'status': 'expires_week', 'message': f'Expires in {days_until_expiry} days', 'days': days_until_expiry}
        else:
            return {'status': 'safe', 'message': f'Expires in {days_until_expiry} days', 'days': days_until_expiry}


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
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    IN_PREPARATION = "IN_PREPARATION"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class OrderType(enum.Enum):
    REGULAR = "REGULAR"
    CATERING = "CATERING"
    ONLINE = "ONLINE"


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


class UserSession(db.Model):
    __tablename__ = 'user_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(500))
    device_info = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))
    
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)
    
    def is_expired(self):
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def update_activity(self):
        self.last_activity = datetime.utcnow()
        db.session.commit()


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
