# 4. Enhanced Tracking System (Week 4)
# Purpose: Full lifecycle tracking with reminders
# scripts/application_tracker.py
"""
Enhanced Application Tracking
Tracks entire application lifecycle with status updates
"""

class ApplicationTracker:
    def __init__(self):
        self.statuses = [
            'discovered', 'scored', 'matched', 'cover_letter_generated',
            'package_created', 'submitted', 'viewed', 'interview_requested',
            'interview_scheduled', 'offer', 'rejected', 'withdrawn'
        ]
        
    def update_status(self, job_id, new_status, notes=''):
        """Update application status with timestamp"""
        applications = self.load_applications()
        
        for app in applications:
            if app['id'] == job_id:
                app['status'] = new_status
                app['status_history'].append({
                    'status': new_status,
                    'timestamp': datetime.now().isoformat(),
                    'notes': notes
                })
                app['last_updated'] = datetime.now().isoformat()
                break
        
        self.save_applications(applications)
        
    def get_follow_up_needed(self):
        """Find applications needing follow-up"""
        applications = self.load_applications()
        needs_follow_up = []
        
        for app in applications:
            if app['status'] == 'submitted':
                days_since = (datetime.now() - datetime.fromisoformat(app['submitted_at'])).days
                
                if days_since >= 7 and not app.get('followed_up'):
                    needs_follow_up.append({
                        'id': app['id'],
                        'company': app['company'],
                        'days_since_submission': days_since,
                        'action': 'Send follow-up email'
                    })
        
        return needs_follow_up
