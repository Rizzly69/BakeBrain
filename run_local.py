#!/usr/bin/env python3
"""
Local development runner for Smart Bakery Management System
This script sets up the environment and runs the application locally
"""

import os
import sys
import subprocess

def setup_environment():
    """Set up the local development environment"""
    
    # Set default environment variables
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///local_bakery.db'
    
    if not os.environ.get('SESSION_SECRET'):
        os.environ['SESSION_SECRET'] = 'dev-secret-key-change-in-production'
    
    print("🏭 Smart Bakery Management System")
    print("=" * 50)
    print("Setting up local development environment...")
    
    # Check if database exists
    if not os.path.exists('local_bakery.db'):
        print("📊 Initializing database...")
        try:
            from setup_database import setup_database
            setup_database()
            print("✅ Database initialized successfully!")
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            print("Please run: python setup_database.py")
            return False
    
    return True

def run_application():
    """Run the Flask application"""
    
    print("\n🚀 Starting Smart Bakery Management System...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🔑 Login with: admin / admin123")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        from main import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements_local.txt")
    except Exception as e:
        print(f"❌ Application error: {e}")

if __name__ == '__main__':
    if setup_environment():
        run_application()
    else:
        print("❌ Setup failed. Please check the error messages above.")
        sys.exit(1)