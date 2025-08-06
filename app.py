import os
import logging

from flask import Flask
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

# Import db from models to avoid circular imports
from models import db

login_manager = LoginManager()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///bakery.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# configure logging
logging.basicConfig(level=logging.DEBUG)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models to ensure tables are created
    from models import *
    import routes
    
    db.create_all()

# Add custom Jinja filters
import json

@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python object"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}

with app.app_context():
    # Create default admin user if it doesn't exist
    from models import User, Role
    from werkzeug.security import generate_password_hash
    
    # Create roles
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role()
        admin_role.name = 'admin'
        admin_role.description = 'Administrator with full access'
        db.session.add(admin_role)
    
    manager_role = Role.query.filter_by(name='manager').first()
    if not manager_role:
        manager_role = Role()
        manager_role.name = 'manager'
        manager_role.description = 'Manager with operational access'
        db.session.add(manager_role)
    
    staff_role = Role.query.filter_by(name='staff').first()
    if not staff_role:
        staff_role = Role()
        staff_role.name = 'staff'
        staff_role.description = 'Staff with limited access'
        db.session.add(staff_role)
    
    customer_role = Role.query.filter_by(name='customer').first()
    if not customer_role:
        customer_role = Role()
        customer_role.name = 'customer'
        customer_role.description = 'Customer with order access'
        db.session.add(customer_role)
    
    db.session.commit()
    
    # Create admin user if it doesn't exist
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User()
        admin_user.username = 'admin'
        admin_user.email = 'admin@bakery.com'
        admin_user.password_hash = generate_password_hash('admin123')
        admin_user.first_name = 'Admin'
        admin_user.last_name = 'User'
        admin_user.role_id = admin_role.id
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
