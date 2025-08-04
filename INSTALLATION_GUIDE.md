# Quick Installation Guide

## Step 1: Extract Files
Extract the downloaded `smart-bakery-management.tar.gz` file to your desired directory.

## Step 2: Install Python Dependencies
```bash
pip install -r requirements_local.txt
```

## Step 3: Set Environment Variables
Create a `.env` file or set environment variables:
```bash
export DATABASE_URL="sqlite:///bakery.db"
export SESSION_SECRET="your-secret-key-here"
```

## Step 4: Initialize Database
```bash
python setup_database.py
```

## Step 5: Run Application
```bash
# Simple run
python run_local.py

# Or direct Flask run
python main.py
```

## Default Login
- Username: `admin`
- Password: `admin123`

## Features to Test
1. **Inventory Management** - Check low stock alerts for products and ingredients
2. **AI Insights** - View demand forecasting and business intelligence
3. **Order Processing** - Create orders and generate PDF invoices
4. **Role Management** - Switch between different user roles
5. **Raw Materials Tracking** - Monitor ingredient inventory and supplier contacts

## Troubleshooting
- Ensure Python 3.9+ is installed
- Check that all dependencies are installed correctly
- Verify database permissions
- Use `python -m flask run` as alternative startup method

The application will be available at `http://localhost:5000`