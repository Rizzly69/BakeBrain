#!/usr/bin/env python3
"""
Test script for inventory integration functionality
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Product, RawProduct, ProductRecipe, Inventory, User, Order, OrderItem, OrderStatus, OrderType

def test_inventory_integration():
    """Test the inventory integration functionality"""
    
    with app.app_context():
        print("Testing Inventory Integration...")
        
        # Test 1: Check if products have recipes
        products = Product.query.all()
        print(f"\n1. Found {len(products)} products")
        
        for product in products:
            max_quantity = product.get_max_orderable_quantity()
            available_inventory = product.get_available_quantity()
            recipe_count = len(product.recipes)
            
            print(f"   - {product.name}:")
            print(f"     Available inventory: {available_inventory}")
            print(f"     Recipe ingredients: {recipe_count}")
            print(f"     Max orderable: {max_quantity}")
            
            if product.recipes:
                print(f"     Recipe details:")
                for recipe in product.recipes:
                    print(f"       - {recipe.raw_product.name}: {recipe.quantity_required} {recipe.unit_of_measure}")
        
        # Test 2: Check raw material consumption
        print(f"\n2. Testing raw material consumption...")
        
        # Get a product with a recipe
        product_with_recipe = Product.query.join(ProductRecipe).first()
        if product_with_recipe:
            print(f"   Testing with product: {product_with_recipe.name}")
            
            # Check current raw material levels
            print(f"   Current raw material levels:")
            for recipe in product_with_recipe.recipes:
                print(f"     - {recipe.raw_product.name}: {recipe.raw_product.current_stock} {recipe.raw_product.unit_of_measure}")
            
            # Test consuming materials for 2 units
            test_quantity = 2
            print(f"   Testing consumption for {test_quantity} units...")
            
            if product_with_recipe.can_make_quantity(test_quantity):
                print(f"   ✓ Can make {test_quantity} units")
                
                # Store original levels
                original_levels = {}
                for recipe in product_with_recipe.recipes:
                    original_levels[recipe.raw_product.id] = recipe.raw_product.current_stock
                
                # Consume materials
                if product_with_recipe.consume_raw_materials(test_quantity):
                    print(f"   ✓ Successfully consumed materials")
                    
                    # Check new levels
                    print(f"   New raw material levels:")
                    for recipe in product_with_recipe.recipes:
                        consumed = original_levels[recipe.raw_product.id] - recipe.raw_product.current_stock
                        print(f"     - {recipe.raw_product.name}: {recipe.raw_product.current_stock} {recipe.raw_product.unit_of_measure} (consumed: {consumed})")
                else:
                    print(f"   ✗ Failed to consume materials")
            else:
                print(f"   ✗ Cannot make {test_quantity} units")
        else:
            print("   No products with recipes found")
        
        # Test 3: Check order validation
        print(f"\n3. Testing order validation...")
        
        # Get a customer
        customer = User.query.join(User.role).filter(User.role.name == 'customer').first()
        if customer:
            print(f"   Testing with customer: {customer.first_name} {customer.last_name}")
            
            # Create a test order
            test_order = Order(
                order_number=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                customer_id=customer.id,
                order_type=OrderType.REGULAR,
                status=OrderStatus.PENDING,
                total_amount=0
            )
            db.session.add(test_order)
            db.session.flush()
            
            # Try to add items to the order
            for product in products[:3]:  # Test first 3 products
                max_quantity = product.get_max_orderable_quantity()
                test_quantity = min(max_quantity, 5)  # Try to order up to 5 units
                
                if test_quantity > 0:
                    print(f"   Testing order for {product.name}: {test_quantity} units")
                    
                    order_item = OrderItem(
                        order_id=test_order.id,
                        product_id=product.id,
                        quantity=test_quantity,
                        unit_price=float(product.price),
                        total_price=float(product.price) * test_quantity
                    )
                    db.session.add(order_item)
                    
                    # Consume raw materials if product has recipe
                    if product.recipes:
                        if product.consume_raw_materials(test_quantity):
                            print(f"     ✓ Successfully consumed raw materials")
                        else:
                            print(f"     ✗ Failed to consume raw materials")
                    else:
                        print(f"     - No recipe, no raw materials consumed")
                else:
                    print(f"   Skipping {product.name}: out of stock")
            
            # Update order total
            test_order.total_amount = sum(item.total_price for item in test_order.items)
            db.session.commit()
            
            print(f"   Test order created: {test_order.order_number}")
            print(f"   Total items: {len(test_order.items)}")
            print(f"   Total amount: ${test_order.total_amount}")
            
            # Clean up test order
            db.session.delete(test_order)
            db.session.commit()
        else:
            print("   No customer found for testing")
        
        print(f"\nInventory integration test completed!")

if __name__ == "__main__":
    test_inventory_integration() 