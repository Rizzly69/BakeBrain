from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField, DecimalField, DateTimeField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from models import Role, Category, Product, OrderStatus, OrderType


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
        self.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]


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
    delivery_date = DateTimeField('Delivery Date', validators=[Optional()])
    delivery_address = TextAreaField('Delivery Address')
    special_instructions = TextAreaField('Special Instructions')
    
    # Catering specific fields
    event_date = DateTimeField('Event Date', validators=[Optional()])
    guest_count = IntegerField('Guest Count', validators=[Optional(), NumberRange(min=1)])
    setup_requirements = TextAreaField('Setup Requirements')
    
    submit = SubmitField('Create Order')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save')
