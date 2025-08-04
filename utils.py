from datetime import datetime, timedelta
import random
import string
from functools import wraps
from flask import abort
from flask_login import current_user
from models import Order, Product, Inventory, AIInsight, OrderStatus
from app import db


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
