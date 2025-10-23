#!/usr/bin/env python3
"""
Application Status Update Manager
==================================
Interactive CLI tool for updating application statuses with:
- Quick status updates
- Bulk status changes
- Status verification
- Automatic reminder creation
- Communication logging
- Interview scheduling
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
from collections import defaultdict

# Import the tracker
sys.path.insert(0, str(Path(__file__).parent))
try:
    from application_tracker_plus import ApplicationTracker
except ImportError:
    print("❌ Cannot import ApplicationTracker. Ensure application_tracker_plus.py is in the same directory.")
    sys.exit(1)


class ApplicationStatusUpdater:
    """Interactive status update manager"""
    
    # Status transitions (valid next statuses)
    VALID_TRANSITIONS = {
        'discovered': ['matched', 'rejected', 'expired'],
        'scored': ['matched', 'rejected'],
        'matched': ['package_created', 'rejected', 'expired'],
        'package_created': ['in_progress', 'rejected', 'withdrawn'],
        'in_progress': ['submitted', 'withdrawn'],
        'submitted': ['viewed', 'screening', 'rejected', 'withdrawn'],
        'viewed': ['screening', 'interview_requested', 'rejected'],
        'screening': ['interview_requested', 'rejected'],
        'interview_requested': ['interview_scheduled', 'rejected', 'withdrawn'],
        'interview_scheduled': ['interview_completed', 'withdrawn'],
        'interview_completed': ['offer_received', 'rejected'],
        'offer_received': ['offer_accepted', 'offer_declined'],
        'offer_accepted': [],  # Terminal state
        'offer_declined': [],  # Terminal state
        'rejected': [],  # Terminal state
        'withdrawn': [],  # Terminal state
        'expired': []  # Terminal state
    }
    
    # Status emojis for better visualization
    STATUS_EMOJIS = {
        'discovered': '🔍',
        'scored': '📊',
        'matched': '✅',
        'package_created': '📦',
        'in_progress': '⏳',
        'submitted': '📤',
        'viewed': '👁️',
        'screening': '🔎',
        'interview_requested': '📧',
        'interview_scheduled': '📅',
        'interview_completed': '✅',
        'offer_received': '🎉',
        'offer_accepted': '🎊',
        'offer_declined': '❌',
        'rejected': '⛔',
        'withdrawn': '🚫',
        'expired': '⏰'
    }
    
    def __init__(self, data_dir: str = 'job_search'):
        self.tracker = ApplicationTracker(data_dir)
        self.data_dir = Path(data_dir)
    
    def display_application(self, app: Dict):
        """Display application details in a formatted way"""
        print(f"\n{'='*70}")
        print(f"📋 {app['company']} - {app['position']}")
        print(f"{'='*70}")
        print(f"ID: {app['id']}")
        print(f"Platform: {app['platform']}")
        print(f"Location: {app['location']}")
        print(f"Salary: {app['salary']}")
        print(f"Current Status: {self.STATUS_EMOJIS.get(app['status'], '❓')} {app['status']}")
        print(f"Created: {self._format_date(app['created_at'])}")
        if app['submitted_at']:
            print(f"Submitted: {self._format_date(app['submitted_at'])}")
        print(f"Last Updated: {self._format_date(app['last_updated'])}")
        
        if app.get('cv_score'):
            print(f"\n📊 CV Match Score: {app['cv_score']}/100")
        
        if app.get('match_reasons'):
            print(f"Match Reasons: {', '.join(app['match_reasons'][:3])}")
        
        # Show recent history
        if app.get('status_history') and len(app['status_history']) > 1:
            print(f"\n📜 Recent History:")
            for entry in app['status_history'][-3:]:
                emoji = self.STATUS_EMOJIS.get(entry['status'], '❓')
                print(f"   {emoji} {entry['status']} - {self._format_date(entry['timestamp'])}")
                if entry.get('notes'):
                    print(f"      Note: {entry['notes']}")
        
        # Show active reminders
        active_reminders = [r for r in app.get('reminders', []) if not r.get('completed')]
        if active_reminders:
            print(f"\n⏰ Active Reminders ({len(active_reminders)}):")
            for reminder in active_reminders[:3]:
                print(f"   • {reminder['message']} (Due: {self._format_date(reminder['due_date'])})")
        
        # Show interviews
        if app.get('interviews'):
            print(f"\n📅 Interviews ({len(app['interviews'])}):")
            for interview in app['interviews'][-2:]:
                print(f"   • {interview['type']} - {interview['date']} ({interview.get('status', 'scheduled')})")
        
        # Show follow-ups
        if app.get('follow_ups'):
            print(f"\n📞 Follow-ups ({len(app['follow_ups'])}):")
            for fu in app['follow_ups'][-2:]:
                print(f"   • {fu['method']} - {self._format_date(fu['timestamp'])}")
        
        print(f"\n🔗 URL: {app.get('url', 'N/A')}")
    
    def _format_date(self, date_str: str) -> str:
        """Format ISO date string to readable format"""
        try:
            dt = datetime.fromisoformat(date_str)
            now = datetime.now()
            delta = now - dt
            
            if delta.days == 0:
                return f"Today at {dt.strftime('%H:%M')}"
            elif delta.days == 1:
                return f"Yesterday at {dt.strftime('%H:%M')}"
            elif delta.days < 7:
                return f"{delta.days} days ago"
            else:
                return dt.strftime('%Y-%m-%d')
        except:
            return date_str
    
    def get_valid_next_statuses(self, current_status: str) -> List[str]:
        """Get valid next statuses for current status"""
        return self.VALID_TRANSITIONS.get(current_status, [])
    
    def update_status_interactive(self, job_id: str):
        """Interactive status update for a single application"""
        app = self.tracker.get_application(job_id)
        
        if not app:
            print(f"❌ Application not found: {job_id}")
            return False
        
        # Display current application
        self.display_application(app)
        
        # Get valid transitions
        current_status = app['status']
        valid_statuses = self.get_valid_next_statuses(current_status)
        
        if not valid_statuses:
            print(f"\n⚠️  Application is in terminal state: {current_status}")
            print("No further status updates available.")
            return False
        
        # Show options
        print(f"\n📝 Available Status Updates:")
        for i, status in enumerate(valid_statuses, 1):
            emoji = self.STATUS_EMOJIS.get(status, '❓')
            print(f"   {i}. {emoji} {status}")
        print(f"   0. Cancel")
        
        # Get selection
        try:
            choice = input("\nSelect new status (number): ").strip()
            
            if choice == '0':
                print("Cancelled.")
                return False
            
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(valid_statuses):
                print("❌ Invalid selection")
                return False
            
            new_status = valid_statuses[choice_idx]
            
        except (ValueError, IndexError):
            print("❌ Invalid input")
            return False
        
        # Get notes
        notes = input(f"\nAdd notes (optional): ").strip()
        
        # Confirm
        print(f"\n🔄 Update Status:")
        print(f"   From: {current_status}")
        print(f"   To: {new_status}")
        if notes:
            print(f"   Notes: {notes}")
        
        confirm = input("\nConfirm update? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Cancelled.")
            return False
        
        # Perform update
        success = self.tracker.update_status(job_id, new_status, notes)
        
        if success:
            print(f"\n✅ Status updated successfully!")
            
            # Handle special status actions
            self._handle_status_actions(app, new_status)
            
            return True
        else:
            print(f"\n❌ Status update failed")
            return False
    
    def _handle_status_actions(self, app: Dict, new_status: str):
        """Handle special actions for certain status transitions"""
        job_id = app['id']
        
        if new_status == 'submitted':
            print("\n📤 Application submitted!")
            print("   Automatic reminders created:")
            print("   • Day 3: Check application status")
            print("   • Day 7: Send follow-up email")
            print("   • Day 14: Final follow-up")
        
        elif new_status == 'interview_requested':
            print("\n📧 Interview requested!")
            response = input("\nSchedule interview now? (y/n): ").strip().lower()
            
            if response == 'y':
                self._schedule_interview_interactive(job_id)
        
        elif new_status == 'offer_received':
            print("\n🎉 Congratulations on the offer!")
            print("\n📋 Next steps:")
            print("   1. Review offer details carefully")
            print("   2. Negotiate if needed")
            print("   3. Set decision deadline")
            
            # Add offer reminder
            days = input("\nDays to respond to offer (default: 7): ").strip()
            try:
                days = int(days) if days else 7
                self.tracker.add_reminder(
                    job_id,
                    "Respond to job offer",
                    (datetime.now() + timedelta(days=days)).isoformat(),
                    priority='high'
                )
                print(f"✅ Reminder set for {days} days")
            except ValueError:
                print("⚠️  Invalid days, no reminder set")
        
        elif new_status in ['rejected', 'withdrawn']:
            print(f"\n📝 Application {new_status}")
            
            # Ask for feedback
            feedback = input("\nAny feedback or lessons learned? (optional): ").strip()
            
            if feedback:
                self.tracker.add_communication(
                    job_id,
                    comm_type='note',
                    direction='internal',
                    content=f"Closure feedback: {feedback}"
                )
                print("✅ Feedback recorded")
    
    def _schedule_interview_interactive(self, job_id: str):
        """Interactive interview scheduling"""
        print("\n📅 Schedule Interview")
        print("="*50)
        
        # Get interview details
        date = input("Interview date (YYYY-MM-DD HH:MM): ").strip()
        
        print("\nInterview types:")
        print("1. Phone screening")
        print("2. Video call")
        print("3. Technical assessment")
        print("4. Onsite interview")
        print("5. Panel interview")
        print("6. Informal chat")
        
        type_choice = input("\nSelect type (1-6): ").strip()
        
        interview_types = {
            '1': 'phone_screening',
            '2': 'video_call',
            '3': 'technical_assessment',
            '4': 'onsite',
            '5': 'panel',
            '6': 'informal_chat'
        }
        
        interview_type = interview_types.get(type_choice, 'video_call')
        
        location = input("Location/Link (optional): ").strip()
        notes = input("Notes (optional): ").strip()
        
        # Add interview
        success = self.tracker.add_interview(
            job_id,
            date,
            interview_type,
            location,
            notes
        )
        
        if success:
            print("\n✅ Interview scheduled!")
            print(f"   Type: {interview_type}")
            print(f"   Date: {date}")
            if location:
                print(f"   Location: {location}")
        else:
            print("\n❌ Failed to schedule interview")
    
    def bulk_update(self, status_filter: str, new_status: str, dry_run: bool = True):
        """Bulk update applications matching criteria"""
        apps = self.tracker.get_applications_by_status(status_filter)
        
        if not apps:
            print(f"📭 No applications found with status: {status_filter}")
            return
        
        print(f"\n{'='*70}")
        print(f"🔄 BULK STATUS UPDATE")
        print(f"{'='*70}")
        print(f"Filter: {status_filter}")
        print(f"New Status: {new_status}")
        print(f"Found: {len(apps)} applications")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        
        # Show applications
        print(f"\n📋 Applications to update:")
        for i, app in enumerate(apps[:10], 1):
            print(f"   {i}. {app['company']} - {app['position']}")
        
        if len(apps) > 10:
            print(f"   ... and {len(apps) - 10} more")
        
        if dry_run:
            print("\n🧪 DRY RUN - No changes will be made")
            return
        
        # Confirm
        print(f"\n⚠️  This will update {len(apps)} applications!")
        confirm = input("Proceed? (type 'yes' to confirm): ").strip().lower()
        
        if confirm != 'yes':
            print("Cancelled.")
            return
        
        # Perform updates
        updated = 0
        failed = 0
        
        notes = input("\nAdd notes for all (optional): ").strip()
        
        for app in apps:
            success = self.tracker.update_status(
                app['id'],
                new_status,
                notes or f"Bulk update from {status_filter}",
                auto_reminders=True
            )
            
            if success:
                updated += 1
                print(f"   ✅ {app['company']}")
            else:
                failed += 1
                print(f"   ❌ {app['company']}")
        
        print(f"\n📊 Bulk Update Complete:")
        print(f"   Updated: {updated}")
        print(f"   Failed: {failed}")
    
    def show_status_summary(self):
        """Show summary of all applications by status"""
        print(f"\n{'='*70}")
        print(f"📊 APPLICATION STATUS SUMMARY")
        print(f"{'='*70}")
        
        status_counts = defaultdict(int)
        for app in self.tracker.applications:
            status_counts[app['status']] += 1
        
        # Group by category
        categories = {
            'Active': self.tracker.STATUS_CATEGORIES['active'],
            'Pending': self.tracker.STATUS_CATEGORIES['pending'],
            'Success': self.tracker.STATUS_CATEGORIES['success'],
            'Closed': self.tracker.STATUS_CATEGORIES['closed']
        }
        
        for category, statuses in categories.items():
            count = sum(status_counts.get(s, 0) for s in statuses)
            if count > 0:
                print(f"\n{category} ({count}):")
                for status in statuses:
                    if status_counts[status] > 0:
                        emoji = self.STATUS_EMOJIS.get(status, '❓')
                        print(f"   {emoji} {status}: {status_counts[status]}")
        
        print(f"\n📈 Total Applications: {len(self.tracker.applications)}")
    
    def list_by_status(self, status: str):
        """List all applications with specific status"""
        apps = self.tracker.get_applications_by_status(status)
        
        if not apps:
            print(f"📭 No applications with status: {status}")
            return
        
        emoji = self.STATUS_EMOJIS.get(status, '❓')
        print(f"\n{emoji} {status.upper()} ({len(apps)} applications)")
        print(f"{'='*70}")
        
        for app in apps:
            days_old = (datetime.now() - datetime.fromisoformat(app['created_at'])).days
            print(f"\n🏢 {app['company']} - {app['position']}")
            print(f"   ID: {app['id']}")
            print(f"   Platform: {app['platform']}")
            print(f"   Age: {days_old} days")
            if app.get('cv_score'):
                print(f"   Score: {app['cv_score']}/100")

class GitHubActionsUpdater(ApplicationStatusUpdater):
    """Extended updater with GitHub Actions specific features"""
    
    def auto_update_from_campaign(self, campaign_results: Dict) -> Dict:
        """Auto-update statuses based on campaign execution results"""
        updates = {
            'status_updates': 0,
            'reminders_created': 0,
            'errors': []
        }
        
        for campaign in campaign_results.get('campaigns', []):
            for platform_result in campaign.get('platforms', []):
                platform = platform_result['platform'].lower()
                
                try:
                    # Get applications for this platform
                    apps = self.tracker.get_applications_by_platform(platform)
                    
                    # Update statuses for successful applications
                    successful_count = platform_result.get('successful', 0)
                    
                    if successful_count > 0:
                        # Get most recent apps
                        recent_apps = sorted(
                            apps,
                            key=lambda x: x['created_at'],
                            reverse=True
                        )[:successful_count]
                        
                        for app in recent_apps:
                            if app['status'] in ['discovered', 'matched', 'package_created']:
                                success = self.tracker.update_status(
                                    app['id'],
                                    'submitted',
                                    f"Campaign: {campaign['name']} via {platform}",
                                    auto_reminders=True
                                )
                                
                                if success:
                                    updates['status_updates'] += 1
                                    # Count reminders created
                                    updates['reminders_created'] += 3  # Standard 3 reminders
                
                except Exception as e:
                    updates['errors'].append(f"{platform}: {str(e)}")
        
        return updates
    
    def generate_github_summary(self) -> str:
        """Generate markdown summary for GitHub Actions"""
        summary = "## Application Status Summary\n\n"
        
        # Count by status
        status_counts = defaultdict(int)
        for app in self.tracker.applications:
            status_counts[app['status']] += 1
        
        # Active applications
        active = sum(
            status_counts[s] 
            for s in self.tracker.STATUS_CATEGORIES['active']
        )
        
        # Pending
        pending = sum(
            status_counts[s] 
            for s in self.tracker.STATUS_CATEGORIES['pending']
        )
        
        summary += f"- **Active Applications:** {active}\n"
        summary += f"- **Pending Response:** {pending}\n"
        summary += f"- **Total Tracked:** {len(self.tracker.applications)}\n\n"
        
        summary += "### Status Breakdown\n\n"
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            emoji = self.STATUS_EMOJIS.get(status, 'â"')
            summary += f"- {emoji} **{status}**: {count}\n"
        
        return summary
                

def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description='Update and manage job application statuses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update single application interactively
  python update_application_status.py --update job_12345
  
  # Show status summary
  python update_application_status.py --summary
  
  # List applications by status
  python update_application_status.py --list submitted
  
  # Bulk update (dry run)
  python update_application_status.py --bulk-update discovered matched --dry-run
  
  # Bulk update (live)
  python update_application_status.py --bulk-update in_progress submitted
        """
    )
    
    parser.add_argument('--update', '-u', help='Job ID to update')
    parser.add_argument('--bulk-update', nargs=2, metavar=('OLD_STATUS', 'NEW_STATUS'),
                       help='Bulk update from OLD_STATUS to NEW_STATUS')
    parser.add_argument('--list', '-l', help='List applications by status')
    parser.add_argument('--summary', '-s', action='store_true', help='Show status summary')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
    parser.add_argument('--data-dir', default='job_search', help='Data directory')
    
    args = parser.parse_args()
    
    # Initialize updater
    updater = ApplicationStatusUpdater(args.data_dir)
    
    # Route commands
    if args.update:
        updater.update_status_interactive(args.update)
    
    elif args.bulk_update:
        old_status, new_status = args.bulk_update
        updater.bulk_update(old_status, new_status, args.dry_run)
    
    elif args.list:
        updater.list_by_status(args.list)
    
    elif args.summary:
        updater.show_status_summary()
    
    else:
        # Interactive mode
        print("""
╔════════════════════════════════════════════════════════════════════╗
║          APPLICATION STATUS UPDATE MANAGER                         ║
╚════════════════════════════════════════════════════════════════════╝

Choose an option:
  1. Update application status
  2. Show status summary
  3. List applications by status
  4. Bulk status update
  0. Exit
""")
        
        while True:
            choice = input("\nSelect option: ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            
            elif choice == '1':
                job_id = input("Enter Job ID: ").strip()
                updater.update_status_interactive(job_id)
            
            elif choice == '2':
                updater.show_status_summary()
            
            elif choice == '3':
                status = input("Enter status: ").strip()
                updater.list_by_status(status)
            
            elif choice == '4':
                old = input("Current status: ").strip()
                new = input("New status: ").strip()
                dry = input("Dry run? (y/n): ").strip().lower() == 'y'
                updater.bulk_update(old, new, dry)
            
            else:
                print("Invalid option")


if __name__ == '__main__':
    main()
