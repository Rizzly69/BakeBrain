# Smart Bakery Management System

## Overview

Smart Bakery Management is a comprehensive web application designed to streamline bakery operations with modern technology. The system provides role-based access control for managing orders, inventory, products, staff, and customer relationships. Built with Flask and featuring a dark neon-themed interface, it includes AI-powered insights for business optimization, real-time inventory tracking, and comprehensive reporting capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with Blueprint-style routing
- **Database ORM**: SQLAlchemy with declarative base for model definitions
- **Authentication**: Flask-Login for session management and user authentication
- **Password Security**: Werkzeug password hashing for secure credential storage
- **Database Configuration**: Flexible database URI with connection pooling and health checks

### Frontend Architecture
- **Template Engine**: Jinja2 templating with component-based layout system
- **UI Framework**: Custom CSS with dark neon theme and responsive grid layouts
- **JavaScript Libraries**: Chart.js for data visualization, Feather Icons for iconography
- **Component Structure**: Modular template components (header, sidebar) for reusable UI elements
- **Mobile Support**: Responsive design with mobile menu functionality

### Database Design
- **User Management**: Role-based access control with User, Role, and permission relationships
- **Product Catalog**: Product and Category models with pricing and inventory linkage
- **Order Processing**: Order and OrderItem models supporting regular and catering order types
- **Inventory Tracking**: Real-time stock level monitoring with low-stock alerts
- **Staff Management**: Employee scheduling and role assignment capabilities
- **Analytics Storage**: AI insights storage for business intelligence features

### Security & Authentication
- **Session Management**: Flask-Login with remember-me functionality
- **Role-Based Access**: Decorator-based route protection with granular permissions
- **Password Security**: Salted password hashing with Werkzeug
- **Environment Variables**: Secure configuration management for secrets and database connections
- **CSRF Protection**: Flask-WTF form validation and CSRF token implementation

### Business Logic Features
- **Order Management**: Multi-type order processing (regular, catering, online)
- **Inventory Control**: Automated low-stock alerts and reorder point management
- **AI Insights**: Demand forecasting and operational optimization recommendations
- **Reporting System**: Comprehensive analytics with data export capabilities
- **Staff Scheduling**: Employee shift management and position coverage tracking

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework and routing
- **SQLAlchemy**: Database ORM and connection management
- **Flask-Login**: User session and authentication management
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: Password hashing and HTTP utilities

### Frontend Libraries
- **Chart.js**: Data visualization and analytics charts
- **Feather Icons**: Scalable vector icon library
- **Custom CSS Framework**: Dark neon theme with responsive grid system

### Database Support
- **SQLite**: Default development database (configurable via DATABASE_URL)
- **PostgreSQL**: Production database support through SQLAlchemy
- **Connection Pooling**: Automated connection management with health checks

### Deployment & Infrastructure
- **ProxyFix Middleware**: Production deployment support for reverse proxy configurations
- **Environment Configuration**: Flexible configuration through environment variables
- **Logging System**: Python logging integration for debugging and monitoring

### AI & Analytics
- **Built-in AI Engine**: Custom demand forecasting and business intelligence
- **Data Export**: Report generation and export functionality
- **Real-time Updates**: Live inventory and order status tracking