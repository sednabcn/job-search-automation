#!/usr/bin/env python3
"""
Emergency Data Repair Script for Application Tracker
Run this once to fix corrupted/incomplete tracking data.

Usage:
    python repair_tracking_data.py [data_dir]
    
Example:
    python repair_tracking_data.py job_search
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def repair_applications_json(file_path: Path) -> dict:
    """
    Repair applications.json file by ensuring all required fields exist.
    
    Returns:
        Dictionary with repair statistics
    """
    print(f"\n{'='*70}")
    print(f"REPAIRING: {file_path}")
    print(f"{'='*70}\n")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return {'status': 'not_found'}
    
    # Load existing data
    try:
        with open(file_path) as f:
            apps = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Cannot parse JSON: {e}")
        return {'status': 'parse_error', 'error': str(e)}
    
    print(f"📊 Loaded {len(apps)} applications")
    
    # Valid statuses
    valid_statuses = [
        'discovered', 'scored', 'matched', 'cover_letter_generated',
        'package_created', 'ready_to_apply', 'submitted', 'viewed',
        'interview_requested', 'interview_scheduled', 'interviewed',
        'offer', 'rejected', 'withdrawn'
    ]
    
    # Statistics
    stats = {
        'total': len(apps),
        'fixed_status': 0,
        'fixed_missing_fields': 0,
        'fixed_history': 0,
        'removed_duplicates': 0,
        'invalid_removed': 0
    }
    
    # Repair each application
    seen_ids = set()
    repaired_apps = []
    
    for idx, app in enumerate(apps, 1):
        print(f"\n[{idx}/{len(apps)}] Processing application...")
        
        # Skip if no ID
        if 'id' not in app:
            print(f"  ⚠️  Missing 'id', attempting to generate...")
            if 'company' in app and 'position' in app:
                import hashlib
                app_string = f"{app.get('company', '')}_{app.get('position', '')}"
                app['id'] = f"job_{hashlib.md5(app_string.encode()).hexdigest()[:12]}"
                print(f"  ✅ Generated ID: {app['id']}")
            else:
                print(f"  ❌ Cannot generate ID, skipping application")
                stats['invalid_removed'] += 1
                continue
        
        # Check for duplicates
        if app['id'] in seen_ids:
            print(f"  ❌ Duplicate ID: {app['id']}, removing")
            stats['removed_duplicates'] += 1
            continue
        seen_ids.add(app['id'])
        
        print(f"  ID: {app['id']}")
        print(f"  Company: {app.get('company', 'MISSING')}")
        
        # Track what we fix
        fixed = []
        
        # Ensure all required fields
        defaults = {
            'company': 'Unknown Company',
            'position': 'Unknown Position',
            'location': 'Unknown',
            'salary': 'Not specified',
            'url': '',
            'platform': 'generic',
            'score': 0,
            'status': 'discovered',
            'package_path': None,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'submitted_at': None,
            'followed_up': False,
            'status_history': [],
            'reminders': [],
            'notes': []
        }
        
        for field, default_value in defaults.items():
            if field not in app:
                app[field] = default_value
                fixed.append(field)
                stats['fixed_missing_fields'] += 1
        
        # Validate and fix status
        if app['status'] not in valid_statuses:
            print(f"  ⚠️  Invalid status: '{app['status']}'")
            app['status'] = 'discovered'
            fixed.append('status')
            stats['fixed_status'] += 1
        
        # Ensure status_history exists
        if not app['status_history']:
            app['status_history'] = [{
                'status': app['status'],
                'timestamp': app.get('created_at', datetime.now().isoformat()),
                'notes': 'Data repaired - initial status'
            }]
            fixed.append('status_history')
            stats['fixed_history'] += 1
        
        if fixed:
            print(f"  🔧 Fixed fields: {', '.join(fixed)}")
            print(f"  ✅ Status: {app['status']}")
        else:
            print(f"  ✅ No issues found")
        
        repaired_apps.append(app)
    
    # Create backup
    backup_path = file_path.parent / f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n📦 Creating backup: {backup_path}")
    with open(backup_path, 'w') as f:
        json.dump(apps, f, indent=2)
    
    # Save repaired data
    print(f"\n💾 Saving repaired data to: {file_path}")
    with open(file_path, 'w') as f:
        json.dump(repaired_apps, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print("REPAIR SUMMARY")
    print(f"{'='*70}")
    print(f"Total applications processed: {stats['total']}")
    print(f"Applications after repair: {len(repaired_apps)}")
    print(f"Fixed status: {stats['fixed_status']}")
    print(f"Fixed missing fields: {stats['fixed_missing_fields']}")
    print(f"Fixed status history: {stats['fixed_history']}")
    print(f"Removed duplicates: {stats['removed_duplicates']}")
    print(f"Removed invalid: {stats['invalid_removed']}")
    print(f"{'='*70}\n")
    
    stats['status'] = 'success'
    stats['repaired_count'] = len(repaired_apps)
    return stats


def repair_analytics_json(file_path: Path) -> dict:
    """Repair analytics.json file."""
    print(f"\n{'='*70}")
    print(f"REPAIRING: {file_path}")
    print(f"{'='*70}\n")
    
    if not file_path.exists():
        print(f"ℹ️  Analytics file not found, creating new one")
        
        analytics = {
            'total_applications': 0,
            'status_counts': {},
            'response_rate': 0.0,
            'interview_rate': 0.0,
            'offer_rate': 0.0,
            'avg_response_time_days': 0.0,
            'daily_stats': {},
            'platform_stats': {},
            'last_updated': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        print(f"✅ Created new analytics file")
        return {'status': 'created'}
    
    try:
        with open(file_path) as f:
            analytics = json.load(f)
        print(f"✅ Analytics file is valid")
        return {'status': 'valid'}
    except json.JSONDecodeError as e:
        print(f"❌ Cannot parse JSON: {e}")
        return {'status': 'parse_error', 'error': str(e)}


def main():
    """Main repair function."""
    print("\n" + "="*70)
    print("APPLICATION TRACKER DATA REPAIR TOOL")
    print("="*70)
    
    # Get data directory
    data_dir = sys.argv[1] if len(sys.argv) > 1 else 'job_search'
    data_path = Path(data_dir)
    
    print(f"\nData directory: {data_path.absolute()}")
    
    if not data_path.exists():
        print(f"\n❌ Directory not found: {data_path}")
        print(f"Creating directory...")
        data_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory created")
    
    # Repair applications.json
    applications_file = data_path / 'applications.json'
    app_results = repair_applications_json(applications_file)
    
    # Repair analytics.json
    analytics_file = data_path / 'analytics.json'
    analytics_results = repair_analytics_json(analytics_file)
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Applications: {app_results.get('status', 'unknown')}")
    if app_results.get('status') == 'success':
        print(f"  - Repaired: {app_results.get('repaired_count', 0)} applications")
        print(f"  - Fixed issues: {app_results.get('fixed_missing_fields', 0) + app_results.get('fixed_status', 0)}")
    print(f"Analytics: {analytics_results.get('status', 'unknown')}")
    print("="*70)
    print("\n✅ Data repair complete!")
    print("\nYou can now run your workflow again.\n")


if __name__ == '__main__':
    main()
