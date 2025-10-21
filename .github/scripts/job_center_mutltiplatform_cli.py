#!/usr/bin/env python3
"""
Multi-Platform Job Search CLI - Enhanced Edition
Unified command-line interface with Application Tracking and Networking
COMPLETE VERSION
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    def list_applications(self, status: Optional[str] = None) -> List[Dict]:
        """List applications, optionally filtered by status"""
        if status:
            return [app for app in self.applications if app['status'] == status]
        return self.applications
    
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
        
        response_rate = 0
        if self.applications:
            responses = status_counts['phone_screen'] + status_counts['interview'] + status_counts['offer']
            response_rate = (responses / len(self.applications)) * 100
        
        return {
            'total_applications': len(self.applications),
            'by_status': dict(status_counts),
            'by_source': dict(source_counts),
            'resume_performance': dict(resume_performance),
            'response_rate': response_rate
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
    
    def list_contacts(self, relationship: Optional[str] = None) -> List[Dict]:
        """List contacts, optionally filtered by relationship strength"""
        if relationship:
            return [c for c in self.contacts if c['relationship_strength'] == relationship]
        return self.contacts
    
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


class MultiPlatformJobSearch:
    """Unified job search across multiple platforms"""
    
    SUPPORTED_PLATFORMS = ['linkedin', 'glassdoor', 'indeed', 'reed']
    
    def __init__(self, config_file: str = 'job-manager-config.yml'):
        self.config_file = config_file
        self.config = self._load_config()
        self.results = {}
    
    def _load_config(self) -> Dict:
        """Load configuration file"""
        try:
            import yaml
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {}
    
    def search_all_platforms(self, 
                            job_positions: List[str],
                            location: str = "London",
                            max_per_platform: int = 50) -> Dict:
        """Search across all enabled platforms"""
        logger.info(f"Starting multi-platform search for: {', '.join(job_positions)}")
        
        platforms = self.config.get('platforms', {})
        
        for platform in self.SUPPORTED_PLATFORMS:
            if platform not in platforms:
                continue
            
            platform_config = platforms[platform]
            max_results = platform_config.get('max_results_per_search', max_per_platform)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Searching {platform.upper()}")
            logger.info(f"{'='*60}")
            
            try:
                jobs = self._search_platform(platform, job_positions, location, max_results)
                self.results[platform] = jobs
                logger.info(f"✅ Found {len(jobs)} jobs on {platform}")
            except Exception as e:
                logger.error(f"❌ {platform} search failed: {str(e)}")
                self.results[platform] = []
        
        return self.results
    
    def _search_platform(self, 
                        platform: str, 
                        job_positions: List[str],
                        location: str,
                        max_results: int) -> List[Dict]:
        """Search a specific platform"""
        
        if platform == 'linkedin':
            return self._search_linkedin(job_positions, location, max_results)
        elif platform == 'glassdoor':
            return self._search_glassdoor(job_positions, location, max_results)
        elif platform == 'indeed':
            return self._search_indeed(job_positions, location, max_results)
        elif platform == 'reed':
            return self._search_reed(job_positions, location, max_results)
        else:
            logger.warning(f"Unknown platform: {platform}")
            return []
    
    def _search_linkedin(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search LinkedIn"""
        try:
            from linkedin_automotion import LinkedInAutomation
            
            linkedin = LinkedInAutomation()
            all_jobs = []
            
            for position in positions:
                jobs = linkedin.search_jobs(position, location, max_results // len(positions))
                all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("LinkedIn scraper not found")
            return []
    
    def _search_glassdoor(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search Glassdoor"""
        try:
            from enhanced_glassdoor_automotion import GlassdoorScraper
            
            glassdoor = GlassdoorScraper()
            all_jobs = []
            
            for position in positions:
                jobs = glassdoor.search_jobs(position, location, max_results // len(positions))
                all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("Glassdoor scraper not found")
            return []
    
    def _search_indeed(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search Indeed"""
        try:
            from indeed_scraper import IndeedScraper
            
            indeed = IndeedScraper()
            all_jobs = []
            
            for position in positions:
                jobs = indeed.search_jobs(position, location, max_results // len(positions))
                all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("Indeed scraper not found")
            return []
    
    def _search_reed(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search Reed"""
        try:
            from reed_scraper import ReedScraper
            import os
            
            # Try API first if key is available
            api_key = os.getenv('REED_API_KEY')
            reed = ReedScraper(api_key=api_key)
            
            all_jobs = []
            
            if api_key:
                logger.info("Using Reed API")
                for position in positions:
                    jobs = reed.search_with_api(position, location, max_results // len(positions))
                    all_jobs.extend(jobs)
            else:
                logger.info("Using Reed web scraping")
                for position in positions:
                    jobs = reed.search_jobs(position, location, max_results // len(positions))
                    all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("Reed scraper not found")
            return []
    
    def merge_results(self) -> List[Dict]:
        """Merge and deduplicate results from all platforms"""
        all_jobs = []
        seen_ids = set()
        
        for platform, jobs in self.results.items():
            for job in jobs:
                # Create unique identifier
                job_id = (job.get('id') or 
                         f"{job.get('company', 'unknown')}_{job.get('title', 'unknown')}")
                
                if job_id not in seen_ids:
                    job['platforms'] = [platform]
                    all_jobs.append(job)
                    seen_ids.add(job_id)
                else:
                    # Job found on multiple platforms
                    for existing_job in all_jobs:
                        existing_id = (existing_job.get('id') or 
                                      f"{existing_job.get('company', 'unknown')}_{existing_job.get('title', 'unknown')}")
                        if existing_id == job_id:
                            existing_job['platforms'].append(platform)
                            break
        
        logger.info(f"\n✅ Total unique jobs found: {len(all_jobs)}")
        
        # Find jobs on multiple platforms
        multi_platform = [j for j in all_jobs if len(j.get('platforms', [])) > 1]
        if multi_platform:
            logger.info(f"   Jobs found on multiple platforms: {len(multi_platform)}")
        
        return all_jobs
    
    def save_results(self, output_file: str = 'all_jobs_combined.json'):
        """Save merged results"""
        merged = self.merge_results()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {len(merged)} jobs to {output_file}")
        
        # Also save platform-specific files
        for platform, jobs in self.results.items():
            platform_file = f"{platform}_jobs.json"
            with open(platform_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"   Saved {len(jobs)} {platform} jobs to {platform_file}")
    
    def print_summary(self):
        """Print search summary"""
        print("\n" + "="*60)
        print("📊 MULTI-PLATFORM SEARCH SUMMARY")
        print("="*60)
        
        for platform, jobs in sorted(self.results.items()):
            print(f"\n{platform.upper()}:")
            print(f"  Total jobs: {len(jobs)}")
            
            if jobs:
                companies = len(set(j.get('company', '') for j in jobs))
                locations = len(set(j.get('location', '') for j in jobs))
                with_salary = sum(1 for j in jobs if j.get('salary'))
                
                print(f"  Unique companies: {companies}")
                print(f"  Locations: {locations}")
                print(f"  With salary info: {with_salary} ({with_salary/len(jobs)*100:.1f}%)")
        
        merged = self.merge_results()
        print(f"\n{'='*60}")
        print(f"TOTAL UNIQUE JOBS: {len(merged)}")
        print(f"{'='*60}\n")


def cmd_search(args):
    """Execute job search command"""
    searcher = MultiPlatformJobSearch(config_file=args.config)
    
    # Determine platforms
    if 'all' in args.platforms:
        platforms_to_search = searcher.SUPPORTED_PLATFORMS
    else:
        platforms_to_search = args.platforms
    
    # Override config with selected platforms
    if not searcher.config.get('platforms'):
        searcher.config['platforms'] = {}
    
    for platform in platforms_to_search:
        if platform not in searcher.config['platforms']:
            searcher.config['platforms'][platform] = {
                'max_results_per_search': args.max_per_platform
            }
    
    # Perform search
    searcher.search_all_platforms(
        args.positions,
        args.location,
        args.max_per_platform
    )
    
    # Save and display results
    searcher.save_results(args.output)
    searcher.print_summary()


def cmd_track_add(args):
    """Add application tracking"""
    tracker = JobSearchTracker(args.directory)
    result = tracker.add_application(
        company=args.company,
        position=args.position,
        url=args.url,
        source=args.source,
        resume_version=args.resume_version or "default",
        cover_letter=args.cover_letter,
        notes=args.notes or ""
    )
    print(json.dumps(result, indent=2))


def cmd_track_update(args):
    """Update application status"""
    tracker = JobSearchTracker(args.directory)
    result = tracker.update_status(args.app_id, args.status, args.notes or "")
    print(json.dumps(result, indent=2))


def cmd_track_list(args):
    """List applications"""
    tracker = JobSearchTracker(args.directory)
    apps = tracker.list_applications(args.status)
    
    print(f"\n{'='*80}")
    print(f"📋 APPLICATIONS ({len(apps)} total)")
    print('='*80)
    
    for app in apps:
        print(f"\n🏢 {app['company']} - {app['position']}")
        print(f"   ID: {app['id']}")
        print(f"   Status: {app['status']}")
        print(f"   Applied: {app['applied_date'][:10]}")
        print(f"   Source: {app['source']}")
        if app['notes']:
            print(f"   Notes: {app['notes']}")


def cmd_track_followups(args):
    """Show follow-ups needed"""
    tracker = JobSearchTracker(args.directory)
    follow_ups = tracker.get_follow_ups()
    
    print(f"\n{'='*80}")
    print(f"⏰ FOLLOW-UPS NEEDED ({len(follow_ups)} total)")
    print('='*80)
    
    if not follow_ups:
        print("\n✅ No follow-ups needed!")
    else:
        for fu in follow_ups:
            print(f"\n🏢 {fu['company']} - {fu['position']}")
            print(f"   ID: {fu['id']}")
            print(f"   Status: {fu['status']}")
            print(f"   Days since applied: {fu['days_since_applied']}")


def cmd_track_stats(args):
    """Show application statistics"""
    tracker = JobSearchTracker(args.directory)
    stats = tracker.get_stats()
    
    print(f"\n{'='*80}")
    print("📊 APPLICATION STATISTICS")
    print('='*80)
    print(f"\nTotal Applications: {stats['total_applications']}")
    print(f"Response Rate: {stats['response_rate']:.1f}%")
    
    print("\n📈 By Status:")
    for status, count in stats['by_status'].items():
        print(f"   {status}: {count}")
    
    print("\n🌐 By Source:")
    for source, count in stats['by_source'].items():
        print(f"   {source}: {count}")
    
    print("\n📄 Resume Performance:")
    for version, data in stats['resume_performance'].items():
        rate = (data['interviews'] / data['sent'] * 100) if data['sent'] > 0 else 0
        print(f"   {version}: {data['sent']} sent, {data['interviews']} interviews ({rate:.1f}%)")


def cmd_network_add(args):
    """Add networking contact"""
    tracker = NetworkingTracker(args.directory)
    result = tracker.add_contact(
        name=args.name,
        company=args.company,
        title=args.title,
        linkedin_url=args.linkedin_url or "",
        email=args.email or "",
        source=args.source or "",
        notes=args.notes or ""
    )
    print(json.dumps(result, indent=2))


def cmd_network_log(args):
    """Log networking interaction"""
    tracker = NetworkingTracker(args.directory)
    result = tracker.log_interaction(args.contact_id, args.interaction_type, args.notes or "")
    print(json.dumps(result, indent=2))


def cmd_network_list(args):
    """List networking contacts"""
    tracker = NetworkingTracker(args.directory)
    contacts = tracker.list_contacts(args.relationship)
    
    print(f"\n{'='*80}")
    print(f"🤝 NETWORKING CONTACTS ({len(contacts)} total)")
    print('='*80)
    
    for contact in contacts:
        print(f"\n👤 {contact['name']} - {contact['title']}")
        print(f"   ID: {contact['id']}")
        print(f"   Company: {contact['company']}")
        print(f"   Relationship: {contact['relationship_strength']}")
        print(f"   Last Contact: {contact['last_contact'][:10]}")
        print(f"   Interactions: {len(contact['interactions'])}")
        if contact['linkedin_url']:
            print(f"   LinkedIn: {contact['linkedin_url']}")


def cmd_network_followups(args):
    """Show network follow-ups needed"""
    tracker = NetworkingTracker(args.directory)
    follow_ups = tracker.get_follow_ups()
    
    print(f"\n{'='*80}")
    print(f"🤝 NETWORK FOLLOW-UPS ({len(follow_ups)} total)")
    print('='*80)
    
    if not follow_ups:
        print("\n✅ No network follow-ups needed!")
    else:
        for fu in follow_ups:
            print(f"\n👤 {fu['name']} at {fu['company']}")
            print(f"   ID: {fu['id']}")
            print(f"   Relationship: {fu['relationship']}")
            print(f"   Days since contact: {fu['days_since_contact']}")
            print(f"   Last interaction: {fu['last_interaction']}")


def cmd_extract_keywords(args):
    """Extract keywords from job postings"""
    from keyword_extractor import KeywordExtractor
    
    # Get positions from args or config
    if args.positions:
        positions = args.positions
    else:
        try:
            import yaml
            with open('job-manager-config.yml', 'r') as f:
                config = yaml.safe_load(f)
            positions = config.get('search', {}).get('target_roles', [])
        except:
            positions = ['Senior Software Engineer', 'Staff Engineer']
    
    # Initialize extractor
    extractor = KeywordExtractor(positions)
    
    # Load and analyze jobs
    jobs = extractor.load_jobs_from_files(args.files)
    if not jobs:
        logger.error("No job files found!")
        sys.exit(1)
    
    extractor.extract_keywords(jobs)
    
    # Generate reports
    extractor.export_analysis_report(args.output)
    
    if args.update_config:
        extractor.generate_config('job-manager-config.yml')
        logger.info("✅ Configuration updated")
    else:
        extractor.generate_config('job-manager-config-preview.yml')
        logger.info("✅ Preview saved to job-manager-config-preview.yml")


def cmd_stats(args):
    """Show job search statistics"""
    stats = defaultdict(dict)
    total_jobs = 0
    
    for pattern in args.files:
        for job_file in Path('.').glob(pattern):
            try:
                platform = job_file.stem.replace('_jobs', '')
                with open(job_file, 'r') as f:
                    jobs = json.load(f)
                
                stats[platform]['total'] = len(jobs)
                stats[platform]['companies'] = len(set(j.get('company', '') for j in jobs))
                stats[platform]['with_salary'] = sum(1 for j in jobs if j.get('salary'))
                
                total_jobs += len(jobs)
            except Exception as e:
                logger.error(f"Error reading {job_file}: {e}")
    
    print("\n" + "="*60)
    print("📊 JOB SEARCH STATISTICS")
    print("="*60)
    
    for platform, data in sorted(stats.items()):
        print(f"\n{platform.upper()}:")
        for key, value in data.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL JOBS: {total_jobs}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Multi-Platform Job Search CLI with Tracking & Networking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Job Search
  %(prog)s search --positions "Senior Engineer" "Tech Lead" --location London
  %(prog)s search --platforms indeed reed --positions "Python Developer"
  
  # Application Tracking
  %(prog)s track add --company "Acme Corp" --position "Senior Dev" --url "..." --source linkedin
  %(prog)s track update --app-id acme_corp_1 --status phone_screen --notes "Scheduled for Monday"
  %(prog)s track list --status applied
  %(prog)s track followups
  %(prog)s track stats
  
  # Networking
  %(prog)s network add --name "John Doe" --company "Tech Co" --title "CTO"
  %(prog)s network log --contact-id john_doe_1 --type coffee_chat --notes "Great conversation"
  %(prog)s network list --relationship strong
  %(prog)s network followups
  
  # Keywords & Stats
  %(prog)s extract-keywords --update-config
  %(prog)s stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # ==================== SEARCH COMMAND ====================
    search_parser = subparsers.add_parser('search', help='Search for jobs')
    search_parser.add_argument('--positions', nargs='+', required=True, help='Job positions')
    search_parser.add_argument('--location', default='London', help='Location')
    search_parser.add_argument('--platforms', nargs='+', 
                              choices=['linkedin', 'glassdoor', 'indeed', 'reed', 'all'],
                              default=['all'], help='Platforms to search')
    search_parser.add_argument('--max-per-platform', type=int, default=50,
                              help='Max results per platform')
    search_parser.add_argument('--output', default='all_jobs_combined.json',
                              help='Output file')
    search_parser.add_argument('--config', default='job-manager-config.yml',
                              help='Config file')
    search_parser.set_defaults(func=cmd_search)
    
    # ==================== TRACKING COMMANDS ====================
    track_parser = subparsers.add_parser('track', help='Application tracking')
    track_subparsers = track_parser.add_subparsers(dest='track_command')
    
    # Track add
    track_add_parser = track_subparsers.add_parser('add', help='Add application')
    track_add_parser.add_argument('--company', required=True)
    track_add_parser.add_argument('--position', required=True)
    track_add_parser.add_argument('--url', required=True)
    track_add_parser.add_argument('--source', required=True)
    track_add_parser.add_argument('--resume-version')
    track_add_parser.add_argument('--cover-letter', action='store_true')
    track_add_parser.add_argument('--notes')
    track_add_parser.add_argument('--directory', default='job_search')
    track_add_parser.set_defaults(func=cmd_track_add)
    
    # Track update
    track_update_parser = track_subparsers.add_parser('update', help='Update status')
    track_update_parser.add_argument('--app-id', required=True)
    track_update_parser.add_argument('--status', required=True,
                                    choices=['applied', 'viewed', 'phone_screen', 
                                           'interview', 'offer', 'rejected', 'ghosted'])
    track_update_parser.add_argument('--notes')
    track_update_parser.add_argument('--directory', default='job_search')
    track_update_parser.set_defaults(func=cmd_track_update)
    
    # Track list
    track_list_parser = track_subparsers.add_parser('list', help='List applications')
    track_list_parser.add_argument('--status')
    track_list_parser.add_argument('--directory', default='job_search')
    track_list_parser.set_defaults(func=cmd_track_list)
    
    # Track followups
    track_followups_parser = track_subparsers.add_parser('followups', help='Show follow-ups')
    track_followups_parser.add_argument('--directory', default='job_search')
    track_followups_parser.set_defaults(func=cmd_track_followups)
    
    # Track stats
    track_stats_parser = track_subparsers.add_parser('stats', help='Show statistics')
    track_stats_parser.add_argument('--directory', default='job_search')
    track_stats_parser.set_defaults(func=cmd_track_stats)
    
    # ==================== NETWORKING COMMANDS ====================
    network_parser = subparsers.add_parser('network', help='Networking management')
    network_subparsers = network_parser.add_subparsers(dest='network_command')
    
    # Network add
    network_add_parser = network_subparsers.add_parser('add', help='Add contact')
    network_add_parser.add_argument('--name', required=True)
    network_add_parser.add_argument('--company', required=True)
    network_add_parser.add_argument('--title', required=True)
    network_add_parser.add_argument('--linkedin-url')
    network_add_parser.add_argument('--email')
    network_add_parser.add_argument('--source')
    network_add_parser.add_argument('--notes')
    network_add_parser.add_argument('--directory', default='job_search')
    network_add_parser.set_defaults(func=cmd_network_add)
    
    # Network log
    network_log_parser = network_subparsers.add_parser('log', help='Log interaction')
    network_log_parser.add_argument('--contact-id', required=True)
    network_log_parser.add_argument('--type', dest='interaction_type', required=True,
                                   choices=['linkedin_message', 'email', 'call', 
                                          'coffee_chat', 'referral_request', 'referral_given'])
    network_log_parser.add_argument('--notes')
    network_log_parser.add_argument('--directory', default='job_search')
    network_log_parser.set_defaults(func=cmd_network_log)
    
    # Network list
    network_list_parser = network_subparsers.add_parser('list', help='List contacts')
    network_list_parser.add_argument('--relationship', choices=['new', 'warm', 'strong'])
    network_list_parser.add_argument('--directory', default='job_search')
    network_list_parser.set_defaults(func=cmd_network_list)
    
    # Network followups
    network_followups_parser = network_subparsers.add_parser('followups', help='Show follow-ups')
    network_followups_parser.add_argument('--directory', default='job_search')
    network_followups_parser.set_defaults(func=cmd_network_followups)
    
    # ==================== KEYWORD EXTRACTION ====================
    extract_parser = subparsers.add_parser('extract-keywords', help='Extract keywords')
    extract_parser.add_argument('--files', nargs='+', default=['*_jobs.json'])
    extract_parser.add_argument('--positions', nargs='+')
    extract_parser.add_argument('--update-config', action='store_true')
    extract_parser.add_argument('--output', default='keyword_analysis_report.json')
    extract_parser.set_defaults(func=cmd_extract_keywords)
    
    # ==================== STATS COMMAND ====================
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--files', nargs='+', default=['*_jobs.json'])
    stats_parser.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
