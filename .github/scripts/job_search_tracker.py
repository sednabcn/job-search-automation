"""
Professional Job Search Command Center
Comprehensive system for managing an effective job search across all channels
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

class JobSearchTracker:
    """Track all job applications and their status"""
    
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.applications_file = self.tracking_dir / "applications.json"
        self.applications = self._load_applications()
    
    def _load_applications(self) -> List[Dict]:
        """Load application history"""
        if not self.applications_file.exists():
            return []
        
        with open(self.applications_file, 'r') as f:
            return json.load(f)
    
    def _save_applications(self):
        """Save application history"""
        with open(self.applications_file, 'w') as f:
            json.dump(self.applications, f, indent=2)
    
    def add_application(self, 
                       company: str,
                       position: str,
                       url: str,
                       source: str,
                       resume_version: str = "default",
                       cover_letter: bool = False,
                       notes: str = "") -> str:
        """
        Add a new job application
        
        Args:
            company: Company name
            position: Job title
            url: Job posting URL
            source: Where you found it (LinkedIn, Indeed, etc.)
            resume_version: Which resume version used
            cover_letter: Whether you included cover letter
            notes: Any notes about the application
            
        Returns:
            Application ID
        """
        app_id = f"{company.lower().replace(' ', '_')}_{len(self.applications) + 1}"
        
        application = {
            'id': app_id,
            'company': company,
            'position': position,
            'url': url,
            'source': source,
            'resume_version': resume_version,
            'cover_letter': cover_letter,
            'applied_date': datetime.now().isoformat(),
            'status': 'applied',
            'follow_up_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'notes': notes,
            'timeline': [{
                'date': datetime.now().isoformat(),
                'event': 'applied',
                'notes': 'Initial application submitted'
            }]
        }
        
        self.applications.append(application)
        self._save_applications()
        
        print(f"Application tracked: {company} - {position}")
        print(f"Follow up reminder set for: {application['follow_up_date'][:10]}")
        
        return app_id
    
    def update_status(self, app_id: str, status: str, notes: str = ""):
        """
        Update application status
        
        Status options: applied, viewed, phone_screen, interview, offer, rejected, ghosted
        """
        for app in self.applications:
            if app['id'] == app_id:
                app['status'] = status
                app['timeline'].append({
                    'date': datetime.now().isoformat(),
                    'event': status,
                    'notes': notes
                })
                
                # Set follow-up dates
                if status == 'phone_screen':
                    app['follow_up_date'] = (datetime.now() + timedelta(days=3)).isoformat()
                elif status == 'interview':
                    app['follow_up_date'] = (datetime.now() + timedelta(days=2)).isoformat()
                
                self._save_applications()
                print(f"Updated {app['company']} - {app['position']} to: {status}")
                return
        
        print(f"Application ID {app_id} not found")
    
    def get_follow_ups(self) -> List[Dict]:
        """Get applications that need follow-up"""
        today = datetime.now().date()
        follow_ups = []
        
        for app in self.applications:
            if app['status'] in ['rejected', 'offer', 'ghosted']:
                continue
            
            follow_up_date = datetime.fromisoformat(app['follow_up_date']).date()
            if follow_up_date <= today:
                days_since = (today - datetime.fromisoformat(app['applied_date']).date()).days
                follow_ups.append({
                    'id': app['id'],
                    'company': app['company'],
                    'position': app['position'],
                    'status': app['status'],
                    'days_since_applied': days_since,
                    'last_event': app['timeline'][-1]['event']
                })
        
        return follow_ups

    def get_stats(self) -> Dict:
        """Get application statistics"""
        status_counts = defaultdict(int)
        source_counts = defaultdict(int)
        resume_performance = defaultdict(lambda: {'sent': 0, 'interviews': 0})

        for app in self.applications:
            status = app.get('status', 'unknown')
            source = app.get('source', 'unknown')
            resume_ver = app.get('resume_version', 'default')

            status_counts[status] += 1
            source_counts[source] += 1

            resume_performance[resume_ver]['sent'] += 1
            if status in ['phone_screen', 'interview', 'offer']:
                resume_performance[resume_ver]['interviews'] += 1

        return {
            'total_applications': len(self.applications),
            'by_status': dict(status_counts),
            'by_source': dict(source_counts),
            'resume_performance': dict(resume_performance),
            'response_rate': (
                (status_counts['phone_screen'] + status_counts['interview'] + status_counts['offer'])
                / len(self.applications) * 100
                if self.applications else 0
            )
        }
    
    def export_to_csv(self, filename: str = "applications_export.csv"):
        """Export applications to CSV"""
        if not self.applications:
            print("No applications to export")
            return
        
        output_file = self.tracking_dir / filename
        
        with open(output_file, 'w', newline='') as f:
            fieldnames = ['company', 'position', 'applied_date', 'status', 
                         'source', 'resume_version', 'url', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for app in self.applications:
                writer.writerow({
                    'company': app['company'],
                    'position': app['position'],
                    'applied_date': app['applied_date'][:10],
                    'status': app['status'],
                    'source': app['source'],
                    'resume_version': app['resume_version'],
                    'url': app['url'],
                    'notes': app['notes']
                })
        
        print(f"Exported {len(self.applications)} applications to {output_file}")


class NetworkingTracker:
    """Track networking contacts and conversations"""
    
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.contacts_file = self.tracking_dir / "network_contacts.json"
        self.contacts = self._load_contacts()
    
    def _load_contacts(self) -> List[Dict]:
        """Load networking contacts"""
        if not self.contacts_file.exists():
            return []
        
        with open(self.contacts_file, 'r') as f:
            return json.load(f)
    
    def _save_contacts(self):
        """Save networking contacts"""
        with open(self.contacts_file, 'w') as f:
            json.dump(self.contacts, f, indent=2)
    
    def add_contact(self,
                   name: str,
                   company: str,
                   title: str,
                   linkedin_url: str = "",
                   email: str = "",
                   source: str = "",
                   notes: str = "") -> str:
        """
        Add a networking contact
        
        Args:
            name: Contact's name
            company: Their company
            title: Their job title
            linkedin_url: LinkedIn profile URL
            email: Email address
            source: How you met (conference, LinkedIn, referral, etc.)
            notes: Initial notes
            
        Returns:
            Contact ID
        """
        contact_id = f"{name.lower().replace(' ', '_')}_{len(self.contacts) + 1}"
        
        contact = {
            'id': contact_id,
            'name': name,
            'company': company,
            'title': title,
            'linkedin_url': linkedin_url,
            'email': email,
            'source': source,
            'added_date': datetime.now().isoformat(),
            'last_contact': datetime.now().isoformat(),
            'next_follow_up': (datetime.now() + timedelta(days=14)).isoformat(),
            'relationship_strength': 'new',  # new, warm, strong
            'notes': notes,
            'interactions': [{
                'date': datetime.now().isoformat(),
                'type': 'added',
                'notes': f'Met via {source}' if source else 'Added to network'
            }]
        }
        
        self.contacts.append(contact)
        self._save_contacts()
        
        print(f"Contact added: {name} ({company})")
        return contact_id
    
    def log_interaction(self, contact_id: str, interaction_type: str, notes: str):
        """
        Log an interaction with a contact
        
        Types: linkedin_message, email, call, coffee_chat, referral_request, referral_given
        """
        for contact in self.contacts:
            if contact['id'] == contact_id:
                contact['interactions'].append({
                    'date': datetime.now().isoformat(),
                    'type': interaction_type,
                    'notes': notes
                })
                contact['last_contact'] = datetime.now().isoformat()
                
                # Update relationship strength
                interaction_count = len(contact['interactions'])
                if interaction_count >= 5:
                    contact['relationship_strength'] = 'strong'
                elif interaction_count >= 2:
                    contact['relationship_strength'] = 'warm'
                
                # Set next follow-up
                if interaction_type in ['coffee_chat', 'call']:
                    contact['next_follow_up'] = (datetime.now() + timedelta(days=30)).isoformat()
                else:
                    contact['next_follow_up'] = (datetime.now() + timedelta(days=14)).isoformat()
                
                self._save_contacts()
                print(f"Logged interaction with {contact['name']}")
                return
        
        print(f"Contact ID {contact_id} not found")
    
    def get_follow_ups(self) -> List[Dict]:
        """Get contacts to follow up with"""
        today = datetime.now().date()
        follow_ups = []
        
        for contact in self.contacts:
            next_follow_up = datetime.fromisoformat(contact['next_follow_up']).date()
            if next_follow_up <= today:
                days_since = (today - datetime.fromisoformat(contact['last_contact']).date()).days
                follow_ups.append({
                    'id': contact['id'],
                    'name': contact['name'],
                    'company': contact['company'],
                    'relationship': contact['relationship_strength'],
                    'days_since_contact': days_since,
                    'last_interaction': contact['interactions'][-1]['type']
                })
        
        return follow_ups
    
    def get_referral_opportunities(self) -> List[Dict]:
        """Get contacts who might give referrals"""
        opportunities = []
        
        for contact in self.contacts:
            if contact['relationship_strength'] in ['warm', 'strong']:
                # Check if we've asked for referral recently
                recent_referral = any(
                    i['type'] == 'referral_request' and
                    (datetime.now() - datetime.fromisoformat(i['date'])).days < 90
                    for i in contact['interactions']
                )
                
                if not recent_referral:
                    opportunities.append({
                        'id': contact['id'],
                        'name': contact['name'],
                        'company': contact['company'],
                        'relationship': contact['relationship_strength'],
                        'interaction_count': len(contact['interactions'])
                    })
        
        return opportunities


class LinkedInStrategy:
    """Manage ethical LinkedIn outreach"""
    
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.linkedin_file = self.tracking_dir / "linkedin_activity.json"
        self.activity = self._load_activity()
        
        self.daily_limit = 5  # Conservative limit
    
    def _load_activity(self) -> List[Dict]:
        """Load LinkedIn activity log"""
        if not self.linkedin_file.exists():
            return []
        
        with open(self.linkedin_file, 'r') as f:
            return json.load(f)
    
    def _save_activity(self):
        """Save LinkedIn activity"""
        with open(self.linkedin_file, 'w') as f:
            json.dump(self.activity, f, indent=2)
    
    def _count_today(self) -> int:
        """Count connection requests sent today"""
        today = datetime.now().date()
        return sum(1 for a in self.activity 
                  if a['type'] == 'connection_request' and
                  datetime.fromisoformat(a['date']).date() == today)
    
    def can_send_request(self) -> tuple[bool, str]:
        """Check if we can send more requests today"""
        count = self._count_today()
        if count >= self.daily_limit:
            return False, f"Daily limit reached ({self.daily_limit})"
        return True, f"{self.daily_limit - count} remaining today"
    
    def log_connection_request(self, name: str, title: str, company: str, 
                              message: str, reason: str):
        """
        Log a LinkedIn connection request
        
        Args:
            name: Person's name
            title: Their title
            company: Their company
            message: Your personalized message
            reason: Why you're connecting
        """
        can_send, status = self.can_send_request()
        if not can_send:
            print(f"Cannot send: {status}")
            return False
        
        self.activity.append({
            'type': 'connection_request',
            'date': datetime.now().isoformat(),
            'name': name,
            'title': title,
            'company': company,
            'message': message,
            'reason': reason,
            'status': 'pending'
        })
        
        self._save_activity()
        print(f"Logged connection request to {name}")
        print(f"Remaining today: {self.daily_limit - self._count_today()}")
        return True
    
    def generate_connection_message(self, name: str, common_ground: str) -> str:
        """Generate a personalized connection message template"""
        templates = {
            'alumni': f"Hi {name}, I noticed we're both alumni of {{school}}. I'd love to connect and learn about your experience at {{company}}.",
            'same_field': f"Hi {name}, I've been following your work in {{field}}. I'd appreciate the opportunity to connect and learn from your experience.",
            'job_posting': f"Hi {name}, I recently applied for the {{position}} role at {{company}}. I'd love to connect and learn more about the team and culture.",
            'mutual_connection': f"Hi {name}, {{mutual_connection}} suggested I reach out. I'd love to connect and learn about your work at {{company}}.",
            'content': f"Hi {name}, I really appreciated your recent post about {{topic}}. Would love to connect and continue the conversation."
        }
        
        return templates.get(common_ground, f"Hi {name}, I'd like to add you to my professional network.")


def main():
    """Example usage"""
    print("Professional Job Search Command Center")
    print("=" * 60)
    
    # Initialize trackers
    job_tracker = JobSearchTracker()
    network_tracker = NetworkingTracker()
    linkedin = LinkedInStrategy()
    
    # Example: Add an application
    print("\n1. Track a new application:")
    job_tracker.add_application(
        company="Example Corp",
        position="Senior Developer",
        url="https://example.com/jobs/123",
        source="LinkedIn",
        resume_version="tech_v2",
        cover_letter=True,
        notes="Referred by John Doe"
    )

     # 🧹 Data Cleanup: Ensure all old applications have a 'status' field
    for app in job_tracker.applications:
        if 'status' not in app:
            app['status'] = 'applied'
    job_tracker._save_applications()
    
    # Example: Get stats
    print("\n2. Application Statistics:")
    stats = job_tracker.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Example: Check follow-ups
    print("\n3. Follow-ups needed:")
    follow_ups = job_tracker.get_follow_ups()
    for fu in follow_ups:
        print(f"  - {fu['company']}: {fu['days_since_applied']} days since applied")
    
    # Example: Add networking contact
    print("\n4. Add networking contact:")
    network_tracker.add_contact(
        name="Jane Smith",
        company="Tech Corp",
        title="Engineering Manager",
        linkedin_url="https://linkedin.com/in/janesmith",
        source="Alumni event",
        notes="Very helpful, offered to review my resume"
    )
    
    # Example: LinkedIn strategy
    print("\n5. LinkedIn connection status:")
    can_send, status = linkedin.can_send_request()
    print(f"  {status}")


if __name__ == "__main__":
    main()
