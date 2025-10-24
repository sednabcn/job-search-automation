#!/usr/bin/env python3
"""
GitHub Actions Status Updater - Updates application statuses from campaign results
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class GitHubActionsUpdater:
    """Updates application statuses based on campaign execution results"""
    
    def __init__(self, data_dir: str = 'job_search'):
        self.data_dir = Path(data_dir)
        self.applications_file = self.data_dir / 'applications.json'
        self.analytics_file = self.data_dir / 'analytics.json'
        
    def load_applications(self) -> List[Dict]:
        """Load existing applications"""
        if not self.applications_file.exists():
            return []
        
        try:
            with open(self.applications_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading applications: {e}")
            return []
    
    def save_applications(self, applications: List[Dict]) -> None:
        """Save updated applications"""
        self.applications_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.applications_file, 'w') as f:
            json.dump(applications, f, indent=2)
    
    def update_analytics(self, updates_count: int) -> None:
        """Update analytics with status update info"""
        analytics = {}
        
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, 'r') as f:
                    analytics = json.load(f)
            except:
                pass
        
        # Update status tracking
        if 'status_updates' not in analytics:
            analytics['status_updates'] = {
                'total_updates': 0,
                'last_update': None,
                'history': []
            }
        
        analytics['status_updates']['total_updates'] += updates_count
        analytics['status_updates']['last_update'] = datetime.now().isoformat()
        analytics['status_updates']['history'].append({
            'timestamp': datetime.now().isoformat(),
            'updates': updates_count
        })
        
        # Keep only last 30 days of history
        if len(analytics['status_updates']['history']) > 30:
            analytics['status_updates']['history'] = analytics['status_updates']['history'][-30:]
        
        self.analytics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
    
    def process_campaign_results(self, campaign_results: Dict[str, Any]) -> int:
        """
        Process campaign execution results and update application statuses
        
        Args:
            campaign_results: Dictionary containing campaign execution results
            
        Returns:
            Number of applications updated
        """
        print("🔄 Processing campaign results for status updates...")
        
        applications = self.load_applications()
        updates_count = 0
        timestamp = datetime.now().isoformat()
        
        # Extract applications from campaigns
        for campaign in campaign_results.get('campaigns', []):
            campaign_name = campaign.get('name', 'unknown')
            
            # Process each platform's results
            for platform_result in campaign.get('platforms', []):
                platform = platform_result.get('platform', 'unknown').lower()
                successful = platform_result.get('successful', 0)
                failed = platform_result.get('failed', 0)
                
                print(f"  📊 {campaign_name} - {platform}: {successful} successful, {failed} failed")
                
                # Update application statuses
                # Match applications by campaign and platform
                for app in applications:
                    # Check if this application matches the campaign
                    if (app.get('campaign') == campaign_name and 
                        app.get('platform', '').lower() == platform):
                        
                        # Update status based on result
                        old_status = app.get('status', 'pending')
                        
                        # Determine new status
                        if app.get('application_id') in platform_result.get('successful_ids', []):
                            new_status = 'submitted'
                        elif app.get('application_id') in platform_result.get('failed_ids', []):
                            new_status = 'failed'
                        else:
                            # For applications without specific IDs, mark as submitted if in successful count
                            if app.get('status') == 'pending' and successful > 0:
                                new_status = 'submitted'
                            else:
                                continue
                        
                        # Update if status changed
                        if old_status != new_status:
                            app['status'] = new_status
                            app['last_updated'] = timestamp
                            
                            # Add status history
                            if 'status_history' not in app:
                                app['status_history'] = []
                            
                            app['status_history'].append({
                                'status': new_status,
                                'timestamp': timestamp,
                                'source': 'campaign_execution'
                            })
                            
                            updates_count += 1
                            print(f"    ✅ Updated: {app.get('job_title', 'Unknown')} - {old_status} → {new_status}")
        
        # Save updated applications
        if updates_count > 0:
            self.save_applications(applications)
            self.update_analytics(updates_count)
            print(f"\n✅ Updated {updates_count} application(s)")
        else:
            print("\nℹ️ No status updates needed")
        
        return updates_count
    
    def repair_missing_statuses(self) -> int:
        """Repair applications with missing or invalid statuses"""
        applications = self.load_applications()
        repairs = 0
        
        valid_statuses = ['pending', 'submitted', 'rejected', 'interviewing', 'offered', 'accepted', 'declined', 'failed']
        
        for app in applications:
            if 'status' not in app or app['status'] not in valid_statuses:
                old_status = app.get('status', 'missing')
                app['status'] = 'pending'
                app['last_updated'] = datetime.now().isoformat()
                repairs += 1
                print(f"  🔧 Repaired: {app.get('job_title', 'Unknown')} - '{old_status}' → 'pending'")
        
        if repairs > 0:
            self.save_applications(applications)
            print(f"✅ Repaired {repairs} application(s)")
        
        return repairs


def main():
    """Main execution for GitHub Actions"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update application statuses from campaign results')
    parser.add_argument('--campaign-results', required=True, help='Campaign results JSON file')
    parser.add_argument('--data-dir', default='job_search', help='Data directory')
    parser.add_argument('--output', default='status_update_results.json', help='Output file')
    parser.add_argument('--repair', action='store_true', help='Repair missing statuses')
    
    args = parser.parse_args()
    
    # Initialize updater
    updater = GitHubActionsUpdater(args.data_dir)
    
    # Repair mode
    if args.repair:
        repairs = updater.repair_missing_statuses()
        result = {
            'repairs': repairs,
            'message': f'Repaired {repairs} applications'
        }
        
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        return 0
    
    # Check if campaign results exist
    campaign_results_path = Path(args.campaign_results)
    if not campaign_results_path.exists():
        print(f"⚠️ Campaign results not found: {args.campaign_results}")
        print("Creating empty results...")
        
        result = {
            'status_updates': 0,
            'message': 'No campaign results to process'
        }
        
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        print("ℹ️ No updates needed")
        return 0
    
    # Load campaign results
    try:
        with open(campaign_results_path, 'r') as f:
            campaign_results = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error loading campaign results: {e}")
        return 1
    
    # Process status updates
    try:
        updates_count = updater.process_campaign_results(campaign_results)
        
        # Save results
        result = {
            'status_updates': updates_count,
            'timestamp': datetime.now().isoformat(),
            'message': f'Updated {updates_count} application statuses'
        }
        
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✅ Status update complete: {updates_count} applications updated")
        return 0
        
    except Exception as e:
        print(f"❌ Error processing campaign results: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

