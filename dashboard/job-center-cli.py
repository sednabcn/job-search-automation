#!/usr/bin/env python3
"""
Professional Job Search Command Center - CLI Version
GitHub Actions compatible version with command-line interface
"""

import json
import csv
import argparse
import sys
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
                       notes: str = "") -> Dict:
        """Add a new job application"""
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
        
        return {
            'success': True,
            'message': f"Application tracked: {company} - {position}",
            'app_id': app_id,
            'follow_up_date': application['follow_up_date'][:10]
        }
    
    def update_status(self, app_id: str, status: str, notes: str = "") -> Dict:
        """Update application status"""
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
                return {
                    'success': True,
                    'message': f"Updated {app['company']} - {app['position']} to: {status}"
                }
        
        return {
            'success': False,
            'message': f"Application ID {app_id} not found"
        }
    
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
            status_counts[app['status']] += 1
            source_counts[app['source']] += 1
            
            resume_ver = app['resume_version']
            resume_performance[resume_ver]['sent'] += 1
            if app['status'] in ['phone_screen', 'interview', 'offer']:
                resume_performance[resume_ver]['interviews'] += 1
        
        return {
            'total_applications': len(self.applications),
            'by_status': dict(status_counts),
            'by_source': dict(source_counts),
            'resume_performance': dict(resume_performance),
            'response_rate': (status_counts['phone_screen'] + status_counts['interview'] + 
                            status_counts['offer']) / len(self.applications) * 100 if self.applications else 0
        }


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
                   notes: str = "") -> Dict:
        """Add a networking contact"""
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
            'relationship_strength': 'new',
            'notes': notes,
            'interactions': [{
                'date': datetime.now().isoformat(),
                'type': 'added',
                'notes': f'Met via {source}' if source else 'Added to network'
            }]
        }
        
        self.contacts.append(contact)
        self._save_contacts()
        
        return {
            'success': True,
            'message': f"Contact added: {name} ({company})",
            'contact_id': contact_id
        }
    
    def log_interaction(self, contact_id: str, interaction_type: str, notes: str) -> Dict:
        """Log an interaction with a contact"""
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
                return {
                    'success': True,
                    'message': f"Logged interaction with {contact['name']}"
                }
        
        return {
            'success': False,
            'message': f"Contact ID {contact_id} not found"
        }
    
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


def cmd_add_application(args):
    """Command: Add new application"""
    tracker = JobSearchTracker(args.directory)
    result = tracker.add_application(
        company=args.company,
        position=args.position,
        url=args.url,
        source=args.source,
        resume_version=args.resume_version,
        cover_letter=args.cover_letter,
        notes=args.notes
    )
    print(json.dumps(result, indent=2))


def cmd_update_status(args):
    """Command: Update application status"""
    tracker = JobSearchTracker(args.directory)
    result = tracker.update_status(args.app_id, args.status, args.notes)
    print(json.dumps(result, indent=2))


def cmd_follow_ups(args):
    """Command: Get follow-ups"""
    tracker = JobSearchTracker(args.directory)
    follow_ups = tracker.get_follow_ups()
    
    print(json.dumps({
        'count': len(follow_ups),
        'follow_ups': follow_ups
    }, indent=2))


def cmd_stats(args):
    """Command: Get statistics"""
    tracker = JobSearchTracker(args.directory)
    stats = tracker.get_stats()
    print(json.dumps(stats, indent=2))


def cmd_add_contact(args):
    """Command: Add networking contact"""
    tracker = NetworkingTracker(args.directory)
    result = tracker.add_contact(
        name=args.name,
        company=args.company,
        title=args.title,
        linkedin_url=args.linkedin_url,
        email=args.email,
        source=args.source,
        notes=args.notes
    )
    print(json.dumps(result, indent=2))


def cmd_log_interaction(args):
    """Command: Log contact interaction"""
    tracker = NetworkingTracker(args.directory)
    result = tracker.log_interaction(args.contact_id, args.interaction_type, args.notes)
    print(json.dumps(result, indent=2))


def cmd_network_follow_ups(args):
    """Command: Get network follow-ups"""
    tracker = NetworkingTracker(args.directory)
    follow_ups = tracker.get_follow_ups()
    
    print(json.dumps({
