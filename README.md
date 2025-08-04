# Smart Bakery Management System

A comprehensive web application for managing bakery operations with role-based access control, AI-powered insights, inventory tracking, and professional PDF generation.

## Features

### Core Functionality
- **Role-Based Access Control**: Admin, Manager, Staff, Customer, and Baker roles
- **Order Management**: Regular orders, catering orders, and online orders
- **Inventory Tracking**: Real-time stock monitoring for products and raw materials
- **Product Management**: Comprehensive product catalog with categories
- **Staff Scheduling**: Employee shift management and position assignments
- **Customer Management**: Customer profiles and order history

### Advanced Features
- **AI-Powered Insights**: Machine learning demand forecasting and business optimization
- **PDF Generation**: Professional invoices, reports, and documentation
- **Raw Materials Tracking**: Comprehensive ingredient inventory with supplier management
- **Low Stock Alerts**: Real-time alerts for both products and ingredients
- **Analytics Dashboard**: Visual charts and business intelligence
- **Responsive Design**: Dark neon theme optimized for all devices

## Installation and Setup

### Prerequisites
- Python 3.9 or higher
- PostgreSQL (optional, SQLite is default)

### Step 1: Clone and Navigate
```bash
# Extract the downloaded zip file
unzip smart-bakery-management.zip
cd smart-bakery-management
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Setup
Create a `.env` file in the project root:
```bash
# Database Configuration
DATABASE_URL=sqlite:///bakery.db
SESSION_SECRET=your-secret-key-here

# Optional: PostgreSQL Configuration
# DATABASE_URL=postgresql://username:password@localhost/bakery_db

# Optional: AI Features (requires Anthropic API key)
# ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Step 5: Initialize Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Step 6: Run the Application
```bash
# Development server
python main.py

# Or using Gunicorn (production)
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Step 7: Access the Application
Open your web browser and navigate to: `http://localhost:5000`

## Default Test Accounts

The system comes with pre-configured test accounts:

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| admin | admin123 | Admin | Full system access |
| manager1 | manager123 | Manager | Operational management |
| staff1 | staff123 | Staff | Limited daily operations |
| customer1 | customer123 | Customer | Order placement and tracking |
| baker1 | baker123 | Baker | Production and inventory |

## System Architecture

### Backend
- **Framework**: Flask with Blueprint-style routing
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Authentication**: Flask-Login with role-based permissions
- **PDF Generation**: ReportLab for professional documents
- **AI Engine**: Custom machine learning algorithms for business insights

### Frontend
- **Templates**: Jinja2 with component-based architecture
- **Styling**: Custom CSS with dark neon theme
- **JavaScript**: Chart.js for analytics, Feather Icons for UI
- **Responsive**: Mobile-optimized design

### Database Schema
- **Users & Roles**: Authentication and authorization
- **Products & Categories**: Product catalog management
- **Orders & Items**: Order processing and tracking
- **Inventory**: Stock management for products and ingredients
- **Staff Scheduling**: Employee management
- **AI Insights**: Business intelligence storage

## Key Features Usage

### Inventory Management
- Navigate to Inventory → View stock levels
- Monitor low stock alerts for products and raw materials
- Track ingredient expiry dates and supplier information
- Use quick restock functionality

### AI Insights
- Visit AI Insights → View demand forecasting
- Analyze customer segmentation data
- Review pricing optimization suggestions
- Monitor predictive maintenance alerts

### Order Processing
- Create orders through Orders → New Order
- Handle catering requests with special requirements
- Generate professional PDF invoices
- Track order status and history

### Reports and Analytics
- Access Reports → Generate custom reports
- Export data in PDF format
- View visual charts and analytics
- Monitor business KPIs

## Customization

### Adding New Features
1. Define models in `models.py`
2. Create routes in `routes.py`
3. Add templates in `templates/`
4. Update navigation in `templates/components/`

### Styling Modifications
- Edit `static/css/style.css` for theme changes
- Modify CSS variables for color scheme
- Add responsive breakpoints as needed

### Database Migration
For production deployments:
1. Set up PostgreSQL database
2. Update DATABASE_URL in environment
3. Run database migrations
4. Import sample data if needed

## Security Notes

### Production Deployment
- Change default passwords immediately
- Use strong SESSION_SECRET
- Enable HTTPS
- Configure proper database permissions
- Set up regular backups

### Environment Variables
- Never commit `.env` files to version control
- Use secure secret management in production
- Rotate API keys regularly

## Troubleshooting

### Common Issues
1. **Database Connection**: Check DATABASE_URL format
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Port Conflicts**: Change port in main.py if 5000 is occupied
4. **Template Errors**: Ensure all templates have proper `{% endblock %}` tags

### Performance Optimization
- Use PostgreSQL for production
- Enable database connection pooling
- Implement caching for frequent queries
- Optimize image assets

## Support

For technical support or feature requests:
- Review the code documentation
- Check database schema in `models.py`
- Examine route definitions in `routes.py`
- Refer to template structure in `templates/`

## License

This project is for educational and demonstration purposes. Customize and extend as needed for your specific bakery management requirements.