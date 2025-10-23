"""
Enhanced Application Tracking System
Tracks entire application lifecycle with status updates, reminders, and analytics
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any


class ApplicationTracker:
    """
    Comprehensive application tracking system with status management,
    reminders, and analytics.
    """
    
    def __init__(self, data_dir: str = 'job_search'):
        """
        Initialize the application tracker.
        
        Args:
            data_dir: Directory to store tracking data
        """
        self.data_dir = Path(data_dir)
        self.applications_file = self.data_dir / 'applications.json'
        self.analytics_file = self.data_dir / 'analytics.json'
        
        # Application lifecycle statuses
        self.statuses = [
            'discovered',              # Job found but not evaluated
            'scored',                  # Job scored by matcher
            'matched',                 # High-quality match identified
            'cover_letter_generated',  # AI cover letter created
            'package_created',         # Full application package ready
            'ready_to_apply',          # Ready for submission
            'submitted',               # Application submitted
            'viewed',                  # Application viewed by recruiter
            'interview_requested',     # Interview request received
            'interview_scheduled',     # Interview scheduled
            'interviewed',             # Interview completed
            'offer',                   # Job offer received
            'rejected',                # Application rejected
            'withdrawn'                # Application withdrawn
        ]
        
        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing applications
        self.applications = self.load_applications()
        self.analytics = self.load_analytics()
    
    def load_applications(self) -> List[Dict[str, Any]]:
        """Load applications from JSON file."""
        if self.applications_file.exists():
            try:
                with open(self.applications_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.applications_file}")
                return []
        return []
    
    def save_applications(self, applications: Optional[List[Dict]] = None) -> None:
        """Save applications to JSON file."""
        if applications is None:
            applications = self.applications
        
        with open(self.applications_file, 'w') as f:
            json.dump(applications, f, indent=2)
    
    def load_analytics(self) -> Dict[str, Any]:
        """Load analytics data."""
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._init_analytics()
        return self._init_analytics()
    
    def _init_analytics(self) -> Dict[str, Any]:
        """Initialize analytics structure."""
        return {
            'total_applications': 0,
            'status_counts': {status: 0 for status in self.statuses},
            'response_rate': 0.0,
            'interview_rate': 0.0,
            'offer_rate': 0.0,
            'avg_response_time_days': 0.0,
            'daily_stats': {},
            'platform_stats': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def save_analytics(self) -> None:
        """Save analytics data."""
        self.analytics['last_updated'] = datetime.now().isoformat()
        with open(self.analytics_file, 'w') as f:
            json.dump(self.analytics, f, indent=2)
    
    def add_application(self, job_id: str, job_data: Dict[str, Any],
                       platform: str = 'generic',
                       package_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a new application to tracking.
        
        Args:
            job_id: Unique job identifier
            job_data: Job posting data
            platform: Application platform (linkedin, indeed, etc.)
            package_path: Path to application package
            
        Returns:
            Created application record
        """
        # Check if already exists
        existing = next((app for app in self.applications if app['id'] == job_id), None)
        if existing:
            print(f"Application {job_id} already exists, updating...")
            return self.update_application(job_id, job_data, package_path)
        
        timestamp = datetime.now().isoformat()
        
        application = {
            'id': job_id,
            'company': job_data.get('company', 'Unknown'),
            'position': job_data.get('title', 'Unknown Position'),
            'location': job_data.get('location', 'Unknown'),
            'salary': job_data.get('salary', 'Not specified'),
            'url': job_data.get('url', ''),
            'platform': platform,
            'score': job_data.get('total_score', 0),
            'status': 'package_created' if package_path else 'discovered',
            'package_path': package_path,
            'created_at': timestamp,
            'last_updated': timestamp,
            'submitted_at': None,
            'followed_up': False,
            'status_history': [{
                'status': 'package_created' if package_path else 'discovered',
                'timestamp': timestamp,
                'notes': 'Application tracked'
            }],
            'reminders': [],
            'notes': []
        }
        
        self.applications.append(application)
        self.save_applications()
        self.update_analytics()
        
        return application
    
    def update_application(self, job_id: str, job_data: Dict[str, Any],
                          package_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update existing application with new data."""
        for app in self.applications:
            if app['id'] == job_id:
                # Update fields
                app['company'] = job_data.get('company', app['company'])
                app['position'] = job_data.get('title', app['position'])
                app['score'] = job_data.get('total_score', app['score'])
                
                if package_path:
                    app['package_path'] = package_path
                    if app['status'] == 'discovered':
                        app['status'] = 'package_created'
                
                app['last_updated'] = datetime.now().isoformat()
                
                self.save_applications()
                return app
        
        return None
    
    def update_status(self, job_id: str, new_status: str,
                     notes: str = '', auto_reminders: bool = False) -> bool:
        """
        Update application status with timestamp and optional reminders.
        
        Args:
            job_id: Application ID
            new_status: New status from self.statuses
            notes: Optional notes about status change
            auto_reminders: Automatically set reminders for certain statuses
            
        Returns:
            True if update successful
        """
        if new_status not in self.statuses:
            print(f"Invalid status: {new_status}")
            return False
        
        for app in self.applications:
            if app['id'] == job_id:
                timestamp = datetime.now().isoformat()
                
                # Update status
                app['status'] = new_status
                app['last_updated'] = timestamp
                
                # Add to history
                app['status_history'].append({
                    'status': new_status,
                    'timestamp': timestamp,
                    'notes': notes
                })
                
                # Special handling for certain statuses
                if new_status == 'submitted':
                    app['submitted_at'] = timestamp
                    if auto_reminders:
                        self.add_reminder(job_id, 
                                        'Follow up on application',
                                        days_from_now=7)
                
                elif new_status == 'interview_scheduled' and auto_reminders:
                    self.add_reminder(job_id,
                                    'Prepare for interview',
                                    days_from_now=1)
                
                elif new_status == 'interviewed' and auto_reminders:
                    self.add_reminder(job_id,
                                    'Send thank you email',
                                    days_from_now=1)
                
                self.save_applications()
                self.update_analytics()
                
                return True
        
        print(f"Application {job_id} not found")
        return False
    
    def add_reminder(self, job_id: str, message: str,
                    due_date: Optional[str] = None,
                    days_from_now: Optional[int] = None) -> bool:
        """
        Add a reminder for an application.
        
        Args:
            job_id: Application ID
            message: Reminder message
            due_date: Due date (ISO format) or None
            days_from_now: Days from now for due date (alternative to due_date)
            
        Returns:
            True if reminder added successfully
        """
        for app in self.applications:
            if app['id'] == job_id:
                if due_date is None and days_from_now:
                    due_date = (datetime.now() + timedelta(days=days_from_now)).isoformat()
                elif due_date is None:
                    due_date = datetime.now().isoformat()
                
                reminder = {
                    'message': message,
                    'due_date': due_date,
                    'created_at': datetime.now().isoformat(),
                    'completed': False
                }
                
                if 'reminders' not in app:
                    app['reminders'] = []
                
                app['reminders'].append(reminder)
                self.save_applications()
                
                return True
        
        return False
    
    def get_applications_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all applications with a specific status."""
        return [app for app in self.applications if app['status'] == status]
    
    def get_follow_up_needed(self, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """
        Find applications needing follow-up.
        
        Args:
            days_threshold: Days since submission to trigger follow-up
            
        Returns:
            List of applications needing follow-up
        """
        needs_follow_up = []
        
        for app in self.applications:
            if app['status'] == 'submitted' and app.get('submitted_at'):
                try:
                    submitted_date = datetime.fromisoformat(app['submitted_at'])
                    days_since = (datetime.now() - submitted_date).days
                    
                    if days_since >= days_threshold and not app.get('followed_up'):
                        needs_follow_up.append({
                            'id': app['id'],
                            'company': app['company'],
                            'position': app['position'],
                            'days_since_submission': days_since,
                            'action': 'Send follow-up email',
                            'priority': 'high' if days_since >= 14 else 'medium'
                        })
                except (ValueError, TypeError):
                    continue
        
        return needs_follow_up
    
    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """Get all due reminders."""
        due_reminders = []
        now = datetime.now()
        
        for app in self.applications:
            if app.get('reminders'):
                for reminder in app['reminders']:
                    if not reminder.get('completed'):
                        try:
                            due_date = datetime.fromisoformat(reminder['due_date'])
                            if due_date <= now:
                                due_reminders.append({
                                    'job_id': app['id'],
                                    'company': app['company'],
                                    'position': app['position'],
                                    'reminder': reminder
                                })
                        except (ValueError, TypeError):
                            continue
        
        return due_reminders
    
    def update_analytics(self) -> None:
        """Update analytics based on current applications."""
        self.analytics['total_applications'] = len(self.applications)
        
        # Count by status
        for status in self.statuses:
            count = len([app for app in self.applications if app['status'] == status])
            self.analytics['status_counts'][status] = count
        
        # Calculate rates
        submitted_count = self.analytics['status_counts']['submitted']
        interviewed_count = sum([
            self.analytics['status_counts']['interview_requested'],
            self.analytics['status_counts']['interview_scheduled'],
            self.analytics['status_counts']['interviewed']
        ])
        offer_count = self.analytics['status_counts']['offer']
        
        if submitted_count > 0:
            self.analytics['response_rate'] = round(
                (interviewed_count / submitted_count) * 100, 2
            )
            self.analytics['interview_rate'] = round(
                (interviewed_count / submitted_count) * 100, 2
            )
            self.analytics['offer_rate'] = round(
                (offer_count / submitted_count) * 100, 2
            )
        
        # Platform stats
        platform_counts = {}
        for app in self.applications:
            platform = app.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        self.analytics['platform_stats'] = platform_counts
        
        # Daily stats
        today = datetime.now().date().isoformat()
        if today not in self.analytics['daily_stats']:
            self.analytics['daily_stats'][today] = {
                'new_applications': 0,
                'packages_created': 0,
                'submitted': 0
            }
        
        self.save_analytics()
    
    def generate_report(self) -> str:
        """Generate a comprehensive tracking report."""
        lines = []
        lines.append("# Application Tracking Report\n")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Summary stats
        lines.append("## Summary Statistics\n")
        lines.append(f"- **Total Applications:** {self.analytics['total_applications']}")
        lines.append(f"- **Response Rate:** {self.analytics['response_rate']}%")
        lines.append(f"- **Interview Rate:** {self.analytics['interview_rate']}%")
        lines.append(f"- **Offer Rate:** {self.analytics['offer_rate']}%\n")
        
        # Status breakdown
        lines.append("## Applications by Status\n")
        for status in self.statuses:
            count = self.analytics['status_counts'].get(status, 0)
            if count > 0:
                lines.append(f"- **{status.replace('_', ' ').title()}:** {count}")
        lines.append("")
        
        # Platform breakdown
        if self.analytics.get('platform_stats'):
            lines.append("## Applications by Platform\n")
            for platform, count in self.analytics['platform_stats'].items():
                lines.append(f"- **{platform.title()}:** {count}")
            lines.append("")
        
        # Recent activity
        recent = sorted(self.applications, 
                       key=lambda x: x.get('last_updated', ''), 
                       reverse=True)[:5]
        
        if recent:
            lines.append("## Recent Activity (Last 5)\n")
            for app in recent:
                lines.append(f"### {app['company']} - {app['position']}")
                lines.append(f"- **Status:** {app['status']}")
                lines.append(f"- **Last Updated:** {app['last_updated']}")
                lines.append(f"- **Score:** {app.get('score', 'N/A')}\n")
        
        # Follow-ups needed
        followups = self.get_follow_up_needed()
        if followups:
            lines.append(f"## Follow-ups Needed ({len(followups)})\n")
            for fu in followups:
                lines.append(f"- **{fu['company']}** - {fu['position']}")
                lines.append(f"  - Days since submission: {fu['days_since_submission']}")
                lines.append(f"  - Priority: {fu['priority']}\n")
        
        # Due reminders
        reminders = self.get_due_reminders()
        if reminders:
            lines.append(f"## Due Reminders ({len(reminders)})\n")
            for r in reminders:
                lines.append(f"- **{r['company']}** - {r['position']}")
                lines.append(f"  - {r['reminder']['message']}\n")
        
        return '\n'.join(lines)


# Example usage
if __name__ == '__main__':
    # Initialize tracker
    tracker = ApplicationTracker('job_search')
    
    # Example: Add application
    job_data = {
        'company': 'Tech Corp',
        'title': 'Senior Software Engineer',
        'location': 'London, UK',
        'salary': '£80,000 - £100,000',
        'url': 'https://example.com/job/123',
        'total_score': 85
    }
    
    app = tracker.add_application(
        job_id='job_123',
        job_data=job_data,
        platform='linkedin',
        package_path='job_search/application_packages/job_123'
    )
    
    # Update status
    tracker.update_status('job_123', 'ready_to_apply', 
                         'Package reviewed and ready', 
                         auto_reminders=True)
    
    # Generate report
    print(tracker.generate_report())
