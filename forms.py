from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField, DecimalField, DateTimeField, BooleanField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from models import Role, Category, Product, OrderStatus, OrderType, RawProduct


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    role_id = SelectField('Role', validators=[DataRequired()], coerce=int)
    is_active = BooleanField('Active')
    submit = SubmitField('Save')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [(r.id, r.name.title()) for r in Role.query.filter_by().all()]


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Description')
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    cost = DecimalField('Cost', validators=[Optional(), NumberRange(min=0)])
    sku = StringField('SKU', validators=[Optional(), Length(max=64)])
    category_id = SelectField('Category', validators=[DataRequired()], coerce=int)
    requires_preparation = BooleanField('Requires Preparation')
    preparation_time = IntegerField('Preparation Time (minutes)', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save')
    
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        try:
            categories = Category.query.filter_by(is_active=True).all()
            if categories:
                self.category_id.choices = [(c.id, c.name) for c in categories]
            else:
                # If no categories exist, create default ones
                from app import app, db
                with app.app_context():
                    default_categories = [
                        ('Breads', 'Fresh baked breads and loaves'),
                        ('Pastries', 'Sweet and savory pastries'),
                        ('Cakes', 'Custom cakes and desserts'),
                        ('Cookies', 'Cookies and biscuits'),
                        ('Beverages', 'Coffee, tea, and other drinks')
                    ]
                    for name, description in default_categories:
                        if not Category.query.filter_by(name=name).first():
                            category = Category(name=name, description=description, is_active=True)
                            db.session.add(category)
                    db.session.commit()
                    # Now get the categories again
                    categories = Category.query.filter_by(is_active=True).all()
                    self.category_id.choices = [(c.id, c.name) for c in categories]
        except Exception as e:
            # Fallback to empty choices if there's any error
            self.category_id.choices = []


class RawProductForm(FlaskForm):
    name = StringField('Raw Product Name', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Description')
    unit_of_measure = SelectField('Unit of Measure', validators=[DataRequired()], 
                                 choices=[
                                     ('kg', 'Kilograms (kg)'),
                                     ('g', 'Grams (g)'),
                                     ('l', 'Liters (L)'),
                                     ('ml', 'Milliliters (mL)'),
                                     ('pieces', 'Pieces'),
                                     ('units', 'Units'),
                                     ('bags', 'Bags'),
                                     ('boxes', 'Boxes'),
                                     ('cans', 'Cans'),
                                     ('bottles', 'Bottles')
                                 ])
    cost_per_unit = DecimalField('Cost per Unit', validators=[DataRequired(), NumberRange(min=0)])
    supplier = StringField('Supplier', validators=[Optional(), Length(max=128)])
    supplier_contact = StringField('Supplier Contact', validators=[Optional(), Length(max=128)])
    location = StringField('Storage Location', validators=[Optional(), Length(max=128)])
    current_stock = DecimalField('Current Stock', validators=[DataRequired(), NumberRange(min=0)])
    min_stock_level = DecimalField('Minimum Stock Level', validators=[DataRequired(), NumberRange(min=0)])
    reorder_point = DecimalField('Reorder Point', validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField('Expiry Date', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save')


class InventoryForm(FlaskForm):
    product_id = SelectField('Product', validators=[DataRequired()], coerce=int)
    quantity = IntegerField('Current Quantity', validators=[DataRequired(), NumberRange(min=0)])
    min_stock_level = IntegerField('Minimum Stock Level', validators=[DataRequired(), NumberRange(min=0)])
    max_stock_level = IntegerField('Maximum Stock Level', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Update Inventory')
    
    def __init__(self, *args, **kwargs):
        super(InventoryForm, self).__init__(*args, **kwargs)
        self.product_id.choices = [(p.id, p.name) for p in Product.query.filter_by(is_active=True).all()]


class OrderForm(FlaskForm):
    customer_id = SelectField('Customer', validators=[DataRequired()], coerce=int)
    order_type = SelectField('Order Type', validators=[DataRequired()], 
                           choices=[(t.value, t.value.title()) for t in OrderType])
    delivery_date = StringField('Delivery Date (YYYY-MM-DD HH:MM)', validators=[Optional()])
    delivery_address = TextAreaField('Delivery Address')
    special_instructions = TextAreaField('Special Instructions')
    
    # Catering specific fields
    event_date = StringField('Event Date (YYYY-MM-DD HH:MM)', validators=[Optional()])
    guest_count = IntegerField('Guest Count', validators=[Optional(), NumberRange(min=1)])
    setup_requirements = TextAreaField('Setup Requirements')
    
    submit = SubmitField('Create Order')
    
    def validate_delivery_date(self, field):
        if field.data:
            try:
                from datetime import datetime
                datetime.strptime(field.data, '%Y-%m-%d %H:%M')
            except ValueError:
                from wtforms.validators import ValidationError
                raise ValidationError('Please enter a valid date and time in format YYYY-MM-DD HH:MM')
    
    def validate_event_date(self, field):
        if field.data:
            try:
                from datetime import datetime
                datetime.strptime(field.data, '%Y-%m-%d %H:%M')
            except ValueError:
                from wtforms.validators import ValidationError
                raise ValidationError('Please enter a valid date and time in format YYYY-MM-DD HH:MM')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save')


class ConfigurationForm(FlaskForm):
    value = StringField('Value', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Configuration')
    
    def __init__(self, config_item=None, *args, **kwargs):
        super(ConfigurationForm, self).__init__(*args, **kwargs)
        if config_item:
            self.config_item = config_item
            # Set field type based on data_type
            if config_item.data_type == 'boolean':
                self.value = BooleanField('Value')
            elif config_item.data_type == 'integer':
                self.value = IntegerField('Value', validators=[DataRequired(), NumberRange(min=0)])
            elif config_item.data_type == 'float':
                self.value = DecimalField('Value', validators=[DataRequired(), NumberRange(min=0)])
            elif config_item.data_type == 'text':
                self.value = TextAreaField('Value', validators=[DataRequired()])
            else:
                self.value = StringField('Value', validators=[DataRequired()])
