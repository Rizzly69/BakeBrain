#!/usr/bin/env python3
"""
Migration script to add schedule modification functionality
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add new columns and tables for schedule modifications"""
    
    # Check if database exists
    db_path = 'instance/bakery.db'
    if not os.path.exists(db_path):
        print("Database not found. Please run the application first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting database migration...")
        
        # Add new columns to staff_schedule table
        print("Adding new columns to staff_schedule table...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(staff_schedule)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE staff_schedule ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("  - Added updated_at column")
        
        if 'is_modified' not in columns:
            cursor.execute("ALTER TABLE staff_schedule ADD COLUMN is_modified BOOLEAN DEFAULT 0")
            print("  - Added is_modified column")
        
        if 'modification_reason' not in columns:
            cursor.execute("ALTER TABLE staff_schedule ADD COLUMN modification_reason TEXT")
            print("  - Added modification_reason column")
        
        if 'modified_by' not in columns:
            cursor.execute("ALTER TABLE staff_schedule ADD COLUMN modified_by INTEGER REFERENCES user(id)")
            print("  - Added modified_by column")
        
        if 'original_schedule_id' not in columns:
            cursor.execute("ALTER TABLE staff_schedule ADD COLUMN original_schedule_id INTEGER REFERENCES staff_schedule(id)")
            print("  - Added original_schedule_id column")
        
        # Create schedule_modification table
        print("Creating schedule_modification table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_modification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER NOT NULL,
                modification_type VARCHAR(32) NOT NULL,
                old_start_time TIME,
                old_end_time TIME,
                old_position VARCHAR(64),
                old_notes TEXT,
                new_start_time TIME,
                new_end_time TIME,
                new_position VARCHAR(64),
                new_notes TEXT,
                reason TEXT,
                modified_by INTEGER NOT NULL,
                modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (schedule_id) REFERENCES staff_schedule (id),
                FOREIGN KEY (modified_by) REFERENCES user (id)
            )
        """)
        print("  - Created schedule_modification table")
        
        # Create indexes for better performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedule_modification_schedule_id ON schedule_modification(schedule_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedule_modification_type ON schedule_modification(modification_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedule_modification_date ON schedule_modification(modified_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_staff_schedule_modified ON staff_schedule(is_modified)")
        print("  - Created indexes")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show table structure
        print("\nUpdated table structure:")
        cursor.execute("PRAGMA table_info(staff_schedule)")
        print("staff_schedule columns:")
        for column in cursor.fetchall():
            print(f"  - {column[1]} ({column[2]})")
        
        cursor.execute("PRAGMA table_info(schedule_modification)")
        print("\nschedule_modification columns:")
        for column in cursor.fetchall():
            print(f"  - {column[1]} ({column[2]})")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 