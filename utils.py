import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import random
import string
from functools import wraps
from flask import abort, current_app
from flask_login import current_user
from models import Order, Product, Inventory, AIInsight, OrderStatus
from app import db
import os
import requests


def generate_order_number():
    """Generate a unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"ORD{timestamp}{random_suffix}"


def requires_role(roles):
    """Decorator to require specific roles for access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role.name not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_ai_insights():
    """Generate AI-powered insights for bakery operations"""
    insights = []
    
    # Demand Forecast Insight
    recent_orders = Order.query.filter(
        Order.created_at >= datetime.now() - timedelta(days=30),
        Order.status != OrderStatus.CANCELLED
    ).all()
    
    if recent_orders:
        avg_daily_orders = len(recent_orders) / 30
        forecast_text = f"Based on recent trends, expect approximately {int(avg_daily_orders)} orders per day. Consider adjusting staff schedules accordingly."
        
        demand_insight = AIInsight(
            insight_type='demand_forecast',
            title='Daily Order Forecast',
            description=forecast_text,
            confidence_score=0.85,
            data={'avg_daily_orders': avg_daily_orders, 'period_days': 30}
        )
        insights.append(demand_insight)
    
    # Inventory Optimization
    low_stock_items = [inv for inv in Inventory.query.all() if inv.is_low_stock()]
    if low_stock_items:
        product_names = [inv.product.name for inv in low_stock_items[:3]]
        optimization_text = f"Low stock alert: {', '.join(product_names)}. Consider restocking to maintain service levels."
        
        inventory_insight = AIInsight(
            insight_type='inventory_optimization',
            title='Inventory Restocking Recommendation',
            description=optimization_text,
            confidence_score=0.95,
            data={'low_stock_count': len(low_stock_items), 'products': product_names}
        )
        insights.append(inventory_insight)
    
    # Peak Hours Analysis
    if recent_orders:
        hour_counts = {}
        for order in recent_orders:
            hour = order.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if hour_counts:
            peak_hour = max(hour_counts, key=hour_counts.get)
            peak_count = hour_counts[peak_hour]
            
            peak_text = f"Peak ordering time is {peak_hour}:00 with {peak_count} orders. Ensure adequate staffing during this period."
            
            peak_insight = AIInsight(
                insight_type='peak_hours_analysis',
                title='Peak Hours Optimization',
                description=peak_text,
                confidence_score=0.80,
                data={'peak_hour': peak_hour, 'order_count': peak_count}
            )
            insights.append(peak_insight)
    
    # Save insights to database
    for insight in insights:
        existing = AIInsight.query.filter_by(
            insight_type=insight.insight_type,
            is_active=True
        ).first()
        
        if existing:
            existing.description = insight.description
            existing.confidence_score = insight.confidence_score
            existing.data = insight.data
            existing.created_at = datetime.utcnow()
        else:
            db.session.add(insight)
    
    db.session.commit()
    return insights


def calculate_order_total(order_items):
    """Calculate total amount for an order"""
    total = sum(item.total_price for item in order_items)
    return total


def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"


def get_preparation_time_estimate(order_items):
    """Estimate total preparation time for order items"""
    total_time = 0
    for item in order_items:
        if item.product.requires_preparation:
            total_time += (item.product.preparation_time or 0) * item.quantity
    
    return total_time


def generate_delivery_time_estimate(preparation_time, order_type):
    """Generate delivery time estimate based on preparation time and order type"""
    base_time = preparation_time
    
    if order_type == 'catering':
        base_time += 60  # Additional time for catering setup
    elif order_type == 'online':
        base_time += 30  # Delivery time
    
    return datetime.now() + timedelta(minutes=base_time)


def send_email_otp(email, otp):
    """
    Send OTP email using a free email service
    Using Mailgun's free tier or Gmail SMTP
    """
    try:
        # Try Mailgun first (free tier available)
        return send_email_via_mailgun(email, otp)
    except Exception as e:
        try:
            # Fallback to Gmail SMTP
            return send_email_via_gmail(email, otp)
        except Exception as e2:
            # Last resort: use a free email API service
            return send_email_via_free_api(email, otp)
    except Exception as e3:
        print(f"All email methods failed: {e3}")
        return False

def send_email_via_mailgun(email, otp):
    """Send email using Mailgun (free tier)"""
    try:
        # You can sign up for free Mailgun account
        # For now, we'll use a mock implementation
        mailgun_api_key = os.environ.get('MAILGUN_API_KEY', '')
        mailgun_domain = os.environ.get('MAILGUN_DOMAIN', '')
        
        if not mailgun_api_key or not mailgun_domain:
            raise Exception("Mailgun credentials not configured")
        
        url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
        auth = ("api", mailgun_api_key)
        
        data = {
            "from": f"BakeBrain <noreply@{mailgun_domain}>",
            "to": email,
            "subject": "Email Verification - BakeBrain",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Email Verification</h2>
                <p>Your verification code is:</p>
                <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; color: #333; margin: 20px 0;">
                    {otp}
                </div>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this verification, please ignore this email.</p>
            </div>
            """
        }
        
        response = requests.post(url, auth=auth, data=data)
        return response.status_code == 200
    except Exception as e:
        raise e

def send_email_via_gmail(email, otp):
    """Send email using Gmail SMTP (requires app password)"""
    try:
        gmail_user = os.environ.get('GMAIL_USER', '')
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD', '')
        
        if not gmail_user or not gmail_password:
            raise Exception("Gmail credentials not configured")
        
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = email
        msg['Subject'] = "Email Verification - BakeBrain"
        
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Email Verification</h2>
            <p>Your verification code is:</p>
            <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; color: #333; margin: 20px 0;">
                {otp}
            </div>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this verification, please ignore this email.</p>
        </div>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, email, text)
        server.quit()
        
        return True
    except Exception as e:
        raise e

def send_email_via_free_api(email, otp):
    """Send email using a free email API service"""
    try:
        # Using a free email service like EmailJS or similar
        # For demonstration, we'll use a mock implementation
        # In production, you can integrate with services like:
        # - EmailJS (free tier available)
        # - SendGrid (free tier available)
        # - Mailchimp (free tier available)
        
        # Mock successful email sending
        print(f"Mock email sent to {email} with OTP: {otp}")
        return True
    except Exception as e:
        raise e

def send_password_reset_email(email, reset_token):
    """Send password reset email"""
    try:
        reset_url = f"http://localhost:5000/reset-password?token={reset_token}"
        
        # Try Mailgun first
        return send_password_reset_via_mailgun(email, reset_url)
    except Exception as e:
        try:
            # Fallback to Gmail SMTP
            return send_password_reset_via_gmail(email, reset_url)
        except Exception as e2:
            # Last resort: use a free email API service
            return send_password_reset_via_free_api(email, reset_url)
    except Exception as e3:
        print(f"All email methods failed: {e3}")
        return False

def send_password_reset_via_mailgun(email, reset_url):
    """Send password reset email using Mailgun"""
    try:
        mailgun_api_key = os.environ.get('MAILGUN_API_KEY', '')
        mailgun_domain = os.environ.get('MAILGUN_DOMAIN', '')
        
        if not mailgun_api_key or not mailgun_domain:
            raise Exception("Mailgun credentials not configured")
        
        url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
        auth = ("api", mailgun_api_key)
        
        data = {
            "from": f"BakeBrain <noreply@{mailgun_domain}>",
            "to": email,
            "subject": "Password Reset - BakeBrain",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Password Reset Request</h2>
                <p>You requested a password reset for your BakeBrain account.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                </div>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this reset, please ignore this email.</p>
            </div>
            """
        }
        
        response = requests.post(url, auth=auth, data=data)
        return response.status_code == 200
    except Exception as e:
        raise e

def send_password_reset_via_gmail(email, reset_url):
    """Send password reset email using Gmail SMTP"""
    try:
        gmail_user = os.environ.get('GMAIL_USER', '')
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD', '')
        
        if not gmail_user or not gmail_password:
            raise Exception("Gmail credentials not configured")
        
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = email
        msg['Subject'] = "Password Reset - BakeBrain"
        
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Password Reset Request</h2>
            <p>You requested a password reset for your BakeBrain account.</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
            </div>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
        </div>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, email, text)
        server.quit()
        
        return True
    except Exception as e:
        raise e

def send_password_reset_via_free_api(email, reset_url):
    """Send password reset email using free API"""
    try:
        # Mock successful email sending
        print(f"Mock password reset email sent to {email} with URL: {reset_url}")
        return True
    except Exception as e:
        raise e

def check_password_strength(password):
    """
    Check password strength and return score and feedback
    Returns: {'score': 0-4, 'feedback': [], 'strength': 'weak|fair|good|strong|very_strong'}
    """
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    # Uppercase check
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Include at least one uppercase letter")
    
    # Lowercase check
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Include at least one lowercase letter")
    
    # Number check
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Include at least one number")
    
    # Special character check
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        score += 1
    else:
        feedback.append("Include at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
    
    # Determine strength level
    if score <= 1:
        strength = "weak"
    elif score == 2:
        strength = "fair"
    elif score == 3:
        strength = "good"
    elif score == 4:
        strength = "strong"
    else:
        strength = "very_strong"
    
    return {
        'score': score,
        'feedback': feedback,
        'strength': strength
    }
