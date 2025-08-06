# Schedule Modifications Feature

This document describes the new schedule modification tracking functionality added to the Smart Bakery Management System.

## Overview

The schedule modifications feature allows managers and administrators to:
- Track all changes made to staff schedules
- View a complete audit trail of schedule modifications
- See visual indicators for modified schedules in the weekly view
- Restore deleted schedules
- Export modification history

## New Features

### 1. Visual Schedule Modification Indicators

**Weekly Schedule View:**
- Modified schedules are highlighted with an orange border and background
- A small edit icon appears in the top-right corner of modified schedule cells
- A "View Changes" button appears for modified schedules

**Visual Indicators:**
- 🟠 Orange border and background for modified schedules
- ✏️ Edit icon indicator
- 📋 History button to view changes

### 2. Modifications Page

**Access:** Navigate to "Modifications" in the sidebar or click "View Modifications" from the weekly schedule page.

**Features:**
- **Filtering:** Filter by staff member, modification type, and date range
- **Statistics:** View counts of total, created, updated, and deleted modifications
- **Detailed View:** See exactly what changed in each modification
- **Restoration:** Restore deleted schedules with one click
- **Export:** Download modification history as CSV

**Modification Types:**
- **Created:** New schedules added
- **Updated:** Existing schedules modified
- **Deleted:** Schedules removed

### 3. Database Changes

**New Tables:**
- `schedule_modification`: Tracks all schedule changes

**Enhanced Tables:**
- `staff_schedule`: Added modification tracking fields

**New Fields in `staff_schedule`:**
- `updated_at`: Timestamp of last update
- `is_modified`: Boolean flag for modified schedules
- `modification_reason`: Text description of why schedule was modified
- `modified_by`: User ID who made the modification
- `original_schedule_id`: Reference to original schedule (for tracking changes)

## How It Works

### Automatic Tracking

The system automatically tracks modifications when:

1. **Creating Schedules:**
   - When a new schedule is added via the staff schedule management page
   - Creates a "created" modification record

2. **Updating Schedules:**
   - When an existing schedule is modified
   - Stores the old values before updating
   - Creates an "updated" modification record
   - Marks the schedule as modified

3. **Deleting Schedules:**
   - When a schedule is removed
   - Creates a "deleted" modification record
   - Stores the deleted schedule information

### Manual Tracking

Managers can also manually track modifications by:
- Adding reasons for changes
- Viewing the complete audit trail
- Restoring accidentally deleted schedules

## Usage Guide

### For Managers

1. **Viewing Modifications:**
   - Go to "Modifications" in the sidebar
   - Use filters to find specific changes
   - Click on any modification to see details

2. **Understanding Schedule Changes:**
   - Look for orange borders in the weekly schedule
   - Click the history button to see what changed
   - Check the modifications page for complete history

3. **Restoring Deleted Schedules:**
   - Go to the modifications page
   - Find the deleted schedule
   - Click the restore button
   - Confirm the restoration

### For Administrators

1. **Audit Trail:**
   - Export modification history for compliance
   - Review all changes made by managers
   - Track who made what changes and when

2. **Data Integrity:**
   - All changes are automatically logged
   - No schedule changes can be made without tracking
   - Complete history is maintained

## Technical Implementation

### Database Schema

```sql
-- Enhanced staff_schedule table
ALTER TABLE staff_schedule ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE staff_schedule ADD COLUMN is_modified BOOLEAN DEFAULT 0;
ALTER TABLE staff_schedule ADD COLUMN modification_reason TEXT;
ALTER TABLE staff_schedule ADD COLUMN modified_by INTEGER REFERENCES user(id);
ALTER TABLE staff_schedule ADD COLUMN original_schedule_id INTEGER REFERENCES staff_schedule(id);

-- New schedule_modification table
CREATE TABLE schedule_modification (
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
);
```

### API Endpoints

- `GET /modifications` - View modifications page
- `POST /api/schedule/restore/<id>` - Restore deleted schedule
- `GET /api/modifications/export` - Export modifications as CSV

### Key Functions

- `track_schedule_modification()` - Automatically logs changes
- `restore_schedule()` - Restores deleted schedules
- `export_modifications()` - Exports modification history

## Migration

To add this functionality to an existing database:

1. Run the migration script:
   ```bash
   python migrate_schedule_modifications.py
   ```

2. The script will:
   - Add new columns to existing tables
   - Create the new modifications table
   - Add necessary indexes for performance

## Benefits

1. **Transparency:** Complete visibility into all schedule changes
2. **Accountability:** Track who made what changes and when
3. **Recovery:** Restore accidentally deleted schedules
4. **Compliance:** Maintain audit trails for regulatory requirements
5. **Efficiency:** Quick identification of modified schedules

## Future Enhancements

Potential improvements for future versions:

1. **Email Notifications:** Alert managers when schedules are modified
2. **Approval Workflow:** Require approval for certain schedule changes
3. **Bulk Operations:** Track modifications for bulk schedule updates
4. **Advanced Filtering:** More sophisticated search and filter options
5. **Mobile Notifications:** Push notifications for schedule changes

## Troubleshooting

### Common Issues

1. **No modifications showing:**
   - Ensure the migration script was run successfully
   - Check that schedules are being created/updated through the web interface
   - Verify database permissions

2. **Visual indicators not appearing:**
   - Clear browser cache
   - Check that the schedule has `is_modified=True`
   - Verify CSS is loading correctly

3. **Restore not working:**
   - Ensure you have admin/manager permissions
   - Check that the modification type is "deleted"
   - Verify the schedule wasn't already restored

### Support

For technical support or questions about the modifications feature, please refer to the main application documentation or contact the development team. 