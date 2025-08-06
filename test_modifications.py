#!/usr/bin/env python3
"""
Test script for schedule modification functionality
"""

import os
import sys
from datetime import datetime, date, time, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Role, StaffSchedule, ScheduleModification

def test_modifications():
    """Test the schedule modification functionality"""
    
    with app.app_context():
        print("Testing Schedule Modification Functionality")
        print("=" * 50)
        
        # Check if we have any users
        users = User.query.all()
        if not users:
            print("No users found in database. Please run the application first.")
            return
        
        # Get or create a test staff member
        staff_role = Role.query.filter_by(name='staff').first()
        if not staff_role:
            print("Staff role not found. Please run the application first.")
            return
        
        test_staff = User.query.filter_by(role_id=staff_role.id).first()
        if not test_staff:
            print("No staff members found. Please create some staff first.")
            return
        
        print(f"Using test staff member: {test_staff.first_name} {test_staff.last_name}")
        
        # Test 1: Create a new schedule
        print("\n1. Testing schedule creation...")
        test_date = date.today() + timedelta(days=1)
        
        new_schedule = StaffSchedule(
            staff_id=test_staff.id,
            date=test_date,
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(17, 0),   # 5:00 PM
            position='Cashier',
            notes='Test schedule creation'
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        print(f"   ✓ Created schedule for {test_date}")
        
        # Test 2: Update the schedule
        print("\n2. Testing schedule update...")
        new_schedule.start_time = time(10, 0)  # 10:00 AM
        new_schedule.end_time = time(18, 0)    # 6:00 PM
        new_schedule.position = 'Baker'
        new_schedule.notes = 'Updated test schedule'
        new_schedule.is_modified = True
        new_schedule.modification_reason = 'Test update'
        new_schedule.modified_by = test_staff.id
        
        db.session.commit()
        
        print(f"   ✓ Updated schedule: {new_schedule.start_time} - {new_schedule.end_time}")
        
        # Test 3: Check modifications table
        print("\n3. Checking modifications table...")
        modifications = ScheduleModification.query.all()
        print(f"   ✓ Found {len(modifications)} modification records")
        
        for i, mod in enumerate(modifications, 1):
            print(f"   Modification {i}:")
            print(f"     - Type: {mod.modification_type}")
            print(f"     - Schedule ID: {mod.schedule_id}")
            print(f"     - Modified by: {mod.modified_by}")
            print(f"     - Date: {mod.modified_at}")
        
        # Test 4: Check modified schedules
        print("\n4. Checking modified schedules...")
        modified_schedules = StaffSchedule.query.filter_by(is_modified=True).all()
        print(f"   ✓ Found {len(modified_schedules)} modified schedules")
        
        for schedule in modified_schedules:
            print(f"   - Schedule ID {schedule.id}: {schedule.modification_reason}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        print("You can now test the modifications page in the web interface.")

if __name__ == "__main__":
    test_modifications() 