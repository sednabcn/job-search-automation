#!/usr/bin/env python3
"""
Application Status Update Module
Core functionality for updating application statuses
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class GitHubActionsUpdater:
    """Updates application statuses based on campaign execution results"""
    
    VALID_STATUSES = [
        'pending', 'submitted', 'rejected', 'interviewing', 
        'offered', 'accepted', 'declined', 'failed', 'withdrawn'
    ]
    
    def __init__(self, data_dir: str = 'job_search'):
        self.data_dir = Path(data_dir)
        self.applications_file = self.data_dir / 'applications.json'
        self.analytics_file = self.data_dir / 'analytics.json'
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_applications(self) -> List[Dict]:
        """Load existing applications from JSON file"""
        if not self.applications_file.exists():
            print(f"⚠️ Applications file not found: {self.applications_file}")
            return []
        
        try:
            with open(self.applications_file, 'r', encoding='utf-8') as f:
                applications = json.load(f)
                
            # Ensure it's a list
            if not isinstance(applications, list):
                print(f"⚠️ Applications file is not a list, returning empty list")
                return []
                
            print(f"📂 Loaded {len(applications)} applications")
            return applications
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing applications JSON: {e}")
            return []
        except Exception as e:
            print(f"❌ Error loading applications: {e}")
            return []
    
    def save_applications(self, applications: List[Dict]) -> bool:
        """Save updated applications to JSON file"""
        try:
            self.applications_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.applications_file, 'w', encoding='utf-8') as f:
                json.dump(applications, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(applications)} applications")
            return True
            
        except Exception as e:
            print(f"❌ Error saving applications: {e}")
            return False
    
    def update_analytics(self, updates_count: int, campaign_name: Optional[str] = None) -> None:
        """Update analytics with status update information"""
        analytics = {}
        
        # Load existing analytics
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, 'r') as f:
                    analytics = json.load(f)
            except:
                analytics = {}
        
        # Initialize status_updates section
        if 'status_updates' not in analytics:
            analytics['status_updates'] = {
                'total_updates': 0,
                'last_update': None,
                'by_campaign': {},
                'history': []
            }
        
        # Update counters
        analytics['status_updates']['total_updates'] += updates_count
        analytics['status_updates']['last_update'] = datetime.now().isoformat()
        
        # Track by campaign
        if campaign_name:
            if campaign_name not in analytics['status_updates']['by_campaign']:
                analytics['status_updates']['by_campaign'][campaign_name] = 0
            analytics['status_updates']['by_campaign'][campaign_name] += updates_count
        
        # Add to history
        analytics['status_updates']['history'].append({
            'timestamp': datetime.now().isoformat(),
            'updates': updates_count,
            'campaign': campaign_name
        })
        
        # Keep only last 100 history entries
        if len(analytics['status_updates']['history']) > 100:
            analytics['status_updates']['history'] = analytics['status_updates']['history'][-100:]
        
        # Save analytics
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(analytics, f, indent=2)
            print(f"📊 Analytics updated")
        except Exception as e:
            print(f"⚠️ Could not update analytics: {e}")
    
    def process_campaign_results(self, campaign_results: Dict[str, Any]) -> int:
        """
        Process campaign execution results and update application statuses
        
        Args:
            campaign_results: Dictionary containing campaign execution results with structure:
                {
                    'campaigns': [
                        {
                            'name': 'campaign_name',
                            'platforms': [
                                {
                                    'platform': 'linkedin',
                                    'applications': 5,
                                    'successful': 4,
                                    'failed': 1,
                                    'successful_ids': [...],
                                    'failed_ids': [...]
                                }
                            ]
                        }
                    ]
                }
        
        Returns:
            Number of applications updated
        """
        print("\n" + "="*70)
        print("🔄 PROCESSING CAMPAIGN RESULTS FOR STATUS UPDATES")
        print("="*70)
        
        applications = self.load_applications()
        
        if not applications:
            print("⚠️ No applications found to update")
            return 0
        
        updates_count = 0
        timestamp = datetime.now().isoformat()
        
        # Process each campaign
        campaigns = campaign_results.get('campaigns', [])
        
        if not campaigns:
            print("ℹ️ No campaigns in results")
            return 0
        
        print(f"\n📋 Processing {len(campaigns)} campaign(s)...\n")
        
        for campaign in campaigns:
            campaign_name = campaign.get('name', 'unknown')
            print(f"📦 Campaign: {campaign_name}")
            
            # Process each platform's results
            for platform_result in campaign.get('platforms', []):
                platform = platform_result.get('platform', 'unknown').lower()
                successful = platform_result.get('successful', 0)
                failed = platform_result.get('failed', 0)
                total = platform_result.get('applications', 0)
                
                print(f"  🔹 {platform.title()}: {successful}/{total} successful, {failed} failed")
                
                successful_ids = set(platform_result.get('successful_ids', []))
                failed_ids = set(platform_result.get('failed_ids', []))
                
                # Update matching applications
                for app in applications:
                    # Check if this application matches
                    app_campaign = app.get('campaign', '')
                    app_platform = app.get('platform', '').lower()
                    app_id = app.get('application_id', '')
                    
                    # Skip if not matching campaign/platform
                    if app_campaign != campaign_name or app_platform != platform:
                        continue
                    
                    old_status = app.get('status', 'pending')
                    new_status = None
                    
                    # Determine new status based on IDs or counts
                    if app_id in successful_ids:
                        new_status = 'submitted'
                    elif app_id in failed_ids:
                        new_status = 'failed'
                    elif not app_id and old_status == 'pending':
                        # No specific ID tracking, use counts as heuristic
                        if successful > 0:
                            new_status = 'submitted'
                    
                    # Update if status should change
                    if new_status and old_status != new_status:
                        app['status'] = new_status
                        app['last_updated'] = timestamp
                        
                        # Add to status history
                        if 'status_history' not in app:
                            app['status_history'] = []
                        
                        app['status_history'].append({
                            'status': new_status,
                            'timestamp': timestamp,
                            'source': 'campaign_execution',
                            'campaign': campaign_name,
                            'platform': platform
                        })
                        
                        updates_count += 1
                        job_title = app.get('job_title', 'Unknown Job')
                        company = app.get('company', 'Unknown Company')
                        print(f"    ✅ {job_title} @ {company}: {old_status} → {new_status}")
        
        # Save if there were updates
        if updates_count > 0:
            if self.save_applications(applications):
                self.update_analytics(updates_count)
                print(f"\n✅ Successfully updated {updates_count} application(s)")
            else:
                print(f"\n❌ Failed to save updates")
                return 0
        else:
            print("\nℹ️ No status updates were needed")
        
        print("="*70 + "\n")
        return updates_count
    
    def repair_missing_statuses(self) -> int:
        """Repair applications with missing or invalid statuses"""
        print("\n🔧 Repairing missing or invalid statuses...")
        
        applications = self.load_applications()
        repairs = 0
        
        for app in applications:
            current_status = app.get('status')
            
            # Check if status is missing or invalid
            if not current_status or current_status not in self.VALID_STATUSES:
                old_status = current_status or 'missing'
                app['status'] = 'pending'
                app['last_updated'] = datetime.now().isoformat()
                
                # Add to history
                if 'status_history' not in app:
                    app['status_history'] = []
                
                app['status_history'].append({
                    'status': 'pending',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'repair',
                    'note': f'Repaired from invalid status: {old_status}'
                })
                
                repairs += 1
                job_title = app.get('job_title', 'Unknown')
                print(f"  🔧 Repaired: {job_title} - '{old_status}' → 'pending'")
        
        if repairs > 0:
            self.save_applications(applications)
            print(f"✅ Repaired {repairs} application(s)")
        else:
            print("✅ No repairs needed - all statuses valid")
        
        return repairs
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get summary of application statuses"""
        applications = self.load_applications()
        summary = {status: 0 for status in self.VALID_STATUSES}
        summary['total'] = len(applications)
        
        for app in applications:
            status = app.get('status', 'pending')
            if status in summary:
                summary[status] += 1
        
        return summary


# Standalone execution
if __name__ == '__main__':
    import sys
    
    # Simple test
    updater = GitHubActionsUpdater()
    
    print("Status Summary:")
    summary = updater.get_status_summary()
    for status, count in summary.items():
        if count > 0:
            print(f"  {status}: {count}")
