# scripts/application_tracker.py
"""
Enhanced Application Tracking System
Full lifecycle tracking with analytics, reminders, and multi-platform support
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


class ApplicationTracker:
    """Enhanced application tracking with lifecycle management"""
    
    # Application lifecycle statuses
    STATUSES = [
        'discovered',           # Job found
        'scored',              # CV scored against job
        'matched',             # Passed matching threshold
        'package_created',     # Application package prepared
        'in_progress',         # Started filling application
        'submitted',           # Application submitted
        'viewed',              # Application viewed by employer
        'screening',           # In screening process
        'interview_requested', # Interview invitation received
        'interview_scheduled', # Interview date set
        'interview_completed', # Interview done
        'offer_received',      # Job offer received
        'offer_accepted',      # Offer accepted
        'offer_declined',      # Offer declined
        'rejected',            # Application rejected
        'withdrawn',           # Application withdrawn
        'expired'              # Job posting expired
    ]
    
    # Status categories
    STATUS_CATEGORIES = {
        'active': ['in_progress', 'submitted', 'viewed', 'screening', 
                   'interview_requested', 'interview_scheduled', 'interview_completed'],
        'pending': ['discovered', 'scored', 'matched', 'package_created'],
        'success': ['offer_received', 'offer_accepted'],
        'closed': ['rejected', 'withdrawn', 'expired', 'offer_declined']
    }
    
    def __init__(self, data_dir: str = 'job_search'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.applications_file = self.data_dir / 'applications.json'
        self.analytics_file = self.data_dir / 'analytics.json'
        self.reminders_file = self.data_dir / 'reminders.json'
        
        self.applications = self.load_applications()
    
    def load_applications(self) -> List[Dict]:
        """Load applications with error handling"""
        if self.applications_file.exists():
            try:
                with open(self.applications_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ Error loading applications, creating backup")
                backup = self.applications_file.with_suffix('.json.bak')
                if self.applications_file.exists():
                    self.applications_file.rename(backup)
                return []
        return []
    
    def save_applications(self):
        """Save applications with backup"""
        # Create backup
        if self.applications_file.exists():
            backup = self.applications_file.with_suffix('.json.bak')
            self.applications_file.rename(backup)
        
        # Save current data
        with open(self.applications_file, 'w') as f:
            json.dump(self.applications, f, indent=2, ensure_ascii=False)
    
    def add_application(
        self, 
        job_id: str,
        job_data: Dict,
        platform: str = 'generic',
        package_path: Optional[str] = None
    ) -> Dict:
        """Add new application to tracker"""
        
        # Check if already exists
        existing = self.get_application(job_id)
        if existing:
            print(f"⚠️ Application {job_id} already exists")
            return existing
        
        application = {
            'id': job_id,
            'platform': platform,
            'company': job_data.get('company', 'Unknown'),
            'position': job_data.get('title', 'Unknown'),
            'location': job_data.get('location', 'Unknown'),
            'url': job_data.get('url', ''),
            'salary': job_data.get('salary', 'Not specified'),
            
            'status': 'discovered',
            'status_history': [{
                'status': 'discovered',
                'timestamp': datetime.now().isoformat(),
                'notes': 'Job discovered and added to tracker'
            }],
            
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'submitted_at': None,
            
            'package_path': package_path,
            'cv_score': job_data.get('cv_score'),
            'match_reasons': job_data.get('match_reasons', []),
            
            'follow_ups': [],
            'interviews': [],
            'communications': [],
            'reminders': [],
            
            'metadata': {
                'source': job_data.get('source', 'manual'),
                'tags': job_data.get('tags', []),
                'priority': job_data.get('priority', 'medium')
            }
        }
        
        self.applications.append(application)
        self.save_applications()
        
        print(f"✅ Application added: {application['company']} - {application['position']}")
        return application
    
    def update_status(
        self, 
        job_id: str, 
        new_status: str, 
        notes: str = '',
        auto_reminders: bool = True
    ) -> bool:
        """Update application status with automatic reminder creation"""
        
        if new_status not in self.STATUSES:
            print(f"❌ Invalid status: {new_status}")
            return False
        
        application = self.get_application(job_id)
        if not application:
            print(f"❌ Application not found: {job_id}")
            return False
        
        # Update status
        old_status = application['status']
        application['status'] = new_status
        application['last_updated'] = datetime.now().isoformat()
        
        # Add to history
        history_entry = {
            'status': new_status,
            'timestamp': datetime.now().isoformat(),
            'notes': notes,
            'previous_status': old_status
        }
        application['status_history'].append(history_entry)
        
        # Special handling for submitted status
        if new_status == 'submitted' and not application['submitted_at']:
            application['submitted_at'] = datetime.now().isoformat()
        
        # Create automatic reminders
        if auto_reminders:
            self._create_auto_reminders(application, new_status)
        
        self.save_applications()
        
        print(f"✅ Status updated: {old_status} → {new_status}")
        return True
    
    def _create_auto_reminders(self, application: Dict, status: str):
        """Create automatic reminders based on status"""
        reminders_to_create = {
            'submitted': [
                (3, 'Check application status'),
                (7, 'Send follow-up email if no response'),
                (14, 'Final follow-up or consider moving on')
            ],
            'interview_scheduled': [
                (1, 'Prepare for interview - research company'),
                (0, 'Interview day - review notes and arrive early')
            ],
            'offer_received': [
                (2, 'Review offer details'),
                (5, 'Respond to offer')
            ]
        }
        
        if status in reminders_to_create:
            for days, message in reminders_to_create[status]:
                reminder_date = datetime.now() + timedelta(days=days)
                self.add_reminder(
                    job_id=application['id'],
                    message=message,
                    due_date=reminder_date.isoformat(),
                    auto_created=True
                )
    
    def add_reminder(
        self,
        job_id: str,
        message: str,
        due_date: str,
        priority: str = 'medium',
        auto_created: bool = False
    ) -> bool:
        """Add reminder for application"""
        application = self.get_application(job_id)
        if not application:
            return False
        
        reminder = {
            'id': f"reminder_{len(application['reminders'])}",
            'message': message,
            'due_date': due_date,
            'priority': priority,
            'created_at': datetime.now().isoformat(),
            'completed': False,
            'auto_created': auto_created
        }
        
        application['reminders'].append(reminder)
        self.save_applications()
        return True
    
    def get_application(self, job_id: str) -> Optional[Dict]:
        """Get application by job ID"""
        for app in self.applications:
            if app['id'] == job_id:
                return app
        return None
    
    def get_applications_by_status(self, status: str) -> List[Dict]:
        """Get all applications with specific status"""
        return [app for app in self.applications if app['status'] == status]
    
    def get_applications_by_platform(self, platform: str) -> List[Dict]:
        """Get all applications for specific platform"""
        return [app for app in self.applications if app['platform'] == platform]
    
    def get_active_applications(self) -> List[Dict]:
        """Get all active applications"""
        active_statuses = self.STATUS_CATEGORIES['active']
        return [app for app in self.applications if app['status'] in active_statuses]
    
    def get_follow_up_needed(self) -> List[Dict]:
        """Find applications needing follow-up"""
        needs_follow_up = []
        now = datetime.now()
        
        for app in self.applications:
            if app['status'] == 'submitted' and app['submitted_at']:
                submitted = datetime.fromisoformat(app['submitted_at'])
                days_since = (now - submitted).days
                
                # Check if follow-up already done
                follow_ups = app.get('follow_ups', [])
                last_followup = follow_ups[-1] if follow_ups else None
                
                if days_since >= 7 and not last_followup:
                    needs_follow_up.append({
                        'id': app['id'],
                        'company': app['company'],
                        'position': app['position'],
                        'days_since_submission': days_since,
                        'action': 'Send follow-up email',
                        'priority': 'high' if days_since >= 14 else 'medium'
                    })
                elif last_followup and days_since >= 14:
                    last_followup_date = datetime.fromisoformat(last_followup['timestamp'])
                    if (now - last_followup_date).days >= 7:
                        needs_follow_up.append({
                            'id': app['id'],
                            'company': app['company'],
                            'position': app['position'],
                            'days_since_submission': days_since,
                            'action': 'Send final follow-up',
                            'priority': 'low'
                        })
        
        return needs_follow_up
    
    def get_due_reminders(self) -> List[Dict]:
        """Get all due reminders"""
        due_reminders = []
        now = datetime.now()
        
        for app in self.applications:
            for reminder in app.get('reminders', []):
                if not reminder['completed']:
                    due_date = datetime.fromisoformat(reminder['due_date'])
                    if due_date <= now:
                        due_reminders.append({
                            'job_id': app['id'],
                            'company': app['company'],
                            'position': app['position'],
                            'reminder': reminder
                        })
        
        return sorted(due_reminders, key=lambda x: x['reminder']['due_date'])
    
    def mark_reminder_complete(self, job_id: str, reminder_id: str) -> bool:
        """Mark reminder as completed"""
        application = self.get_application(job_id)
        if not application:
            return False
        
        for reminder in application['reminders']:
            if reminder['id'] == reminder_id:
                reminder['completed'] = True
                reminder['completed_at'] = datetime.now().isoformat()
                self.save_applications()
                return True
        return False
    
    def add_follow_up(self, job_id: str, method: str, notes: str = '') -> bool:
        """Record follow-up action"""
        application = self.get_application(job_id)
        if not application:
            return False
        
        follow_up = {
            'timestamp': datetime.now().isoformat(),
            'method': method,  # email, phone, linkedin, etc.
            'notes': notes
        }
        
        application['follow_ups'].append(follow_up)
        self.save_applications()
        return True
    
    def add_interview(
        self,
        job_id: str,
        interview_date: str,
        interview_type: str,
        location: str = '',
        notes: str = ''
    ) -> bool:
        """Add interview details"""
        application = self.get_application(job_id)
        if not application:
            return False
        
        interview = {
            'date': interview_date,
            'type': interview_type,  # phone, video, onsite, technical, etc.
            'location': location,
            'notes': notes,
            'status': 'scheduled',
            'added_at': datetime.now().isoformat()
        }
        
        application['interviews'].append(interview)
        
        # Auto-update status if needed
        if application['status'] not in ['interview_scheduled', 'interview_completed']:
            self.update_status(job_id, 'interview_scheduled', 
                             f"{interview_type} interview scheduled for {interview_date}")
        
        self.save_applications()
        return True
    
    def add_communication(
        self,
        job_id: str,
        comm_type: str,
        direction: str,
        content: str,
        contact_person: str = ''
    ) -> bool:
        """Log communication"""
        application = self.get_application(job_id)
        if not application:
            return False
        
        communication = {
            'timestamp': datetime.now().isoformat(),
            'type': comm_type,  # email, phone, linkedin, etc.
            'direction': direction,  # inbound, outbound
            'contact_person': contact_person,
            'content': content
        }
        
        application['communications'].append(communication)
        self.save_applications()
        return True
    
    def generate_analytics(self) -> Dict:
        """Generate comprehensive analytics"""
        analytics = {
            'generated_at': datetime.now().isoformat(),
            'total_applications': len(self.applications),
            'by_status': defaultdict(int),
            'by_platform': defaultdict(int),
            'by_company': defaultdict(int),
            'response_rates': {},
            'time_metrics': {},
            'conversion_funnel': {}
        }
        
        # Status distribution
        for app in self.applications:
            analytics['by_status'][app['status']] += 1
            analytics['by_platform'][app['platform']] += 1
            analytics['by_company'][app['company']] += 1
        
        # Calculate response rate
        submitted = len([a for a in self.applications if a['status'] in 
                        ['submitted', 'viewed', 'screening', 'interview_requested',
                         'interview_scheduled', 'interview_completed', 'offer_received']])
        responses = len([a for a in self.applications if a['status'] in
                        ['viewed', 'screening', 'interview_requested', 
                         'interview_scheduled', 'interview_completed', 'offer_received']])
        
        analytics['response_rates']['submitted'] = submitted
        analytics['response_rates']['responded'] = responses
        analytics['response_rates']['rate'] = (responses / submitted * 100) if submitted > 0 else 0
        
        # Time to response metrics
        response_times = []
        for app in self.applications:
            if app['submitted_at'] and app['status'] in ['viewed', 'interview_requested']:
                submitted = datetime.fromisoformat(app['submitted_at'])
                for entry in app['status_history']:
                    if entry['status'] in ['viewed', 'interview_requested']:
                        responded = datetime.fromisoformat(entry['timestamp'])
                        days = (responded - submitted).days
                        response_times.append(days)
                        break
        
        if response_times:
            analytics['time_metrics']['avg_response_days'] = statistics.mean(response_times)
            analytics['time_metrics']['median_response_days'] = statistics.median(response_times)
            analytics['time_metrics']['min_response_days'] = min(response_times)
            analytics['time_metrics']['max_response_days'] = max(response_times)
        
        # Conversion funnel
        funnel_stages = [
            'discovered', 'matched', 'submitted', 'viewed', 
            'interview_requested', 'offer_received'
        ]
        for stage in funnel_stages:
            count = len([a for a in self.applications if a['status'] == stage or
                        any(h['status'] == stage for h in a['status_history'])])
            analytics['conversion_funnel'][stage] = count
        
        # Save analytics
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        return analytics
    
    def generate_report(self, output_format: str = 'markdown') -> str:
        """Generate comprehensive report"""
        analytics = self.generate_analytics()
        
        if output_format == 'markdown':
            return self._generate_markdown_report(analytics)
        elif output_format == 'html':
            return self._generate_html_report(analytics)
        else:
            return json.dumps(analytics, indent=2)
    
    def _generate_markdown_report(self, analytics: Dict) -> str:
        """Generate markdown report"""
        report = f"""# Job Application Tracker Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overview
- **Total Applications:** {analytics['total_applications']}
- **Active Applications:** {sum(analytics['by_status'].get(s, 0) for s in self.STATUS_CATEGORIES['active'])}
- **Pending Applications:** {sum(analytics['by_status'].get(s, 0) for s in self.STATUS_CATEGORIES['pending'])}
- **Response Rate:** {analytics['response_rates']['rate']:.1f}%

## Status Distribution

| Status | Count |
|--------|-------|
"""
        for status, count in sorted(analytics['by_status'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {status} | {count} |\n"
        
        report += f"""
## Platform Distribution

| Platform | Count |
|----------|-------|
"""
        for platform, count in sorted(analytics['by_platform'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {platform} | {count} |\n"
        
        if analytics['time_metrics']:
            report += f"""
## Response Time Metrics
- **Average:** {analytics['time_metrics'].get('avg_response_days', 0):.1f} days
- **Median:** {analytics['time_metrics'].get('median_response_days', 0):.1f} days
- **Range:** {analytics['time_metrics'].get('min_response_days', 0)} - {analytics['time_metrics'].get('max_response_days', 0)} days
"""
        
        report += f"""
## Conversion Funnel

| Stage | Count |
|-------|-------|
"""
        for stage, count in analytics['conversion_funnel'].items():
            report += f"| {stage} | {count} |\n"
        
        # Add follow-ups needed
        follow_ups = self.get_follow_up_needed()
        if follow_ups:
            report += f"""
## Follow-ups Needed ({len(follow_ups)})

| Company | Position | Days Since | Action |
|---------|----------|------------|--------|
"""
            for fu in follow_ups:
                report += f"| {fu['company']} | {fu['position']} | {fu['days_since_submission']} | {fu['action']} |\n"
        
        # Add due reminders
        reminders = self.get_due_reminders()
        if reminders:
            report += f"""
## Due Reminders ({len(reminders)})

| Company | Position | Reminder |
|---------|----------|----------|
"""
            for r in reminders:
                report += f"| {r['company']} | {r['position']} | {r['reminder']['message']} |\n"
        
        return report
    
    def _generate_html_report(self, analytics: Dict) -> str:
        """Generate HTML report"""
        # Simplified HTML report
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Job Application Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .metric {{ background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Job Application Tracker Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    
    <div class="metric">
        <h2>Overview</h2>
        <p><strong>Total Applications:</strong> {analytics['total_applications']}</p>
        <p><strong>Response Rate:</strong> {analytics['response_rates']['rate']:.1f}%</p>
    </div>
</body>
</html>"""
        return html
    
    def export_to_csv(self, output_file: str = 'applications_export.csv'):
        """Export applications to CSV"""
        import csv
        
        output_path = self.data_dir / output_file
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not self.applications:
                return
            
            # Get all possible keys
            fieldnames = ['id', 'company', 'position', 'platform', 'status', 
                         'created_at', 'submitted_at', 'cv_score', 'location', 
                         'salary', 'url']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.applications)
        
        print(f"✅ Exported to {output_path}")


def main():
    """Example usage"""
    tracker = ApplicationTracker()
    
    # Example: Add application
    job = {
        'id': 'job_12345',
        'title': 'Senior Software Engineer',
        'company': 'Tech Corp',
        'location': 'London, UK',
        'salary': '£60,000 - £80,000',
        'url': 'https://example.com/jobs/12345',
        'cv_score': 85,
        'match_reasons': ['Python', 'AWS', 'Leadership']
    }
    
    tracker.add_application('job_12345', job, platform='linkedin')
    
    # Update status
    tracker.update_status('job_12345', 'submitted', 'Applied via Easy Apply')
    
    # Generate report
    report = tracker.generate_report()
    print(report)
    
    # Check follow-ups
    follow_ups = tracker.get_follow_up_needed()
    print(f"\nFollow-ups needed: {len(follow_ups)}")


if __name__ == '__main__':
    main()
