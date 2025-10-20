"""
Job Board Monitor & Alert System
Automated job search across multiple platforms
"""

import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional
from urllib.parse import urlencode

class JobBoardMonitor:
    """Monitor job boards for relevant positions"""
    
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.jobs_file = self.tracking_dir / "discovered_jobs.json"
        self.saved_searches_file = self.tracking_dir / "saved_searches.json"
        
        self.discovered_jobs = self._load_discovered_jobs()
        self.saved_searches = self._load_saved_searches()
    
    def _load_discovered_jobs(self) -> List[Dict]:
        """Load previously discovered jobs"""
        if not self.jobs_file.exists():
            return []
        
        with open(self.jobs_file, 'r') as f:
            return json.load(f)
    
    def _load_saved_searches(self) -> List[Dict]:
        """Load saved search configurations"""
        if not self.saved_searches_file.exists():
            return []
        
        with open(self.saved_searches_file, 'r') as f:
            return json.load(f)
    
    def _save_jobs(self):
        """Save discovered jobs"""
        with open(self.jobs_file, 'w') as f:
            json.dump(self.discovered_jobs, f, indent=2)
    
    def _save_searches(self):
        """Save search configurations"""
        with open(self.saved_searches_file, 'w') as f:
            json.dump(self.saved_searches, f, indent=2)
    
    def add_search(self,
                   name: str,
                   keywords: List[str],
                   location: str = "",
                   remote: bool = False,
                   boards: List[str] = None,
                   min_salary: int = 0,
                   experience_level: str = "mid") -> str:
        """
        Add a saved job search
        
        Args:
            name: Search name
            keywords: Job title keywords
            location: Location (or leave empty for remote)
            remote: Search for remote jobs
            boards: Which job boards to search (linkedin, indeed, glassdoor, etc.)
            min_salary: Minimum salary filter
            experience_level: entry, mid, senior, lead
            
        Returns:
            Search ID
        """
        search_id = hashlib.md5(f"{name}{datetime.now()}".encode()).hexdigest()[:8]
        
        if boards is None:
            boards = ["linkedin", "indeed", "glassdoor"]
        
        search = {
            'id': search_id,
            'name': name,
            'keywords': keywords,
            'location': location,
            'remote': remote,
            'boards': boards,
            'min_salary': min_salary,
            'experience_level': experience_level,
            'created': datetime.now().isoformat(),
            'last_checked': None,
            'jobs_found': 0
        }
        
        self.saved_searches.append(search)
        self._save_searches()
        
        print(f"Search saved: {name} (ID: {search_id})")
        return search_id
    
    def generate_search_urls(self, search_id: str) -> Dict[str, str]:
        """
        Generate search URLs for different job boards
        
        Args:
            search_id: Search configuration ID
            
        Returns:
            Dictionary of board name -> search URL
        """
        search = next((s for s in self.saved_searches if s['id'] == search_id), None)
        if not search:
            return {}
        
        keywords_str = " ".join(search['keywords'])
        urls = {}
        
        # LinkedIn
        if 'linkedin' in search['boards']:
            params = {
                'keywords': keywords_str,
                'location': search['location'],
                'f_WT': '2' if search['remote'] else ''  # Remote filter
            }
            query = urlencode({k: v for k, v in params.items() if v})
            urls['linkedin'] = f"https://www.linkedin.com/jobs/search/?{query}"
        
        # Indeed
        if 'indeed' in search['boards']:
            params = {
                'q': keywords_str,
                'l': search['location'],
                'remotejob': '1' if search['remote'] else ''
            }
            query = urlencode({k: v for k, v in params.items() if v})
            urls['indeed'] = f"https://www.indeed.com/jobs?{query}"
        
        # Glassdoor
        if 'glassdoor' in search['boards']:
            location_str = search['location'].replace(' ', '-').replace(',', '')
            keywords_clean = keywords_str.replace(' ', '-')
            urls['glassdoor'] = f"https://www.glassdoor.com/Job/{location_str}-{keywords_clean}-jobs-SRCH_IL.htm"
        
        # Remote-focused boards
        if search['remote']:
            urls['weworkremotely'] = f"https://weworkremotely.com/remote-jobs/search?term={keywords_str.replace(' ', '+')}"
            urls['remoteok'] = f"https://remoteok.com/remote-{keywords_str.replace(' ', '-')}-jobs"
            urls['flexjobs'] = f"https://www.flexjobs.com/search?search={keywords_str.replace(' ', '+')}"
        
        return urls
    
    def add_discovered_job(self,
                          title: str,
                          company: str,
                          url: str,
                          source: str,
                          location: str = "",
                          salary: str = "",
                          posted_date: str = "",
                          description: str = "") -> bool:
        """
        Add a newly discovered job
        
        Returns:
            True if new job, False if duplicate
        """
        # Check for duplicates
        job_hash = hashlib.md5(f"{company}{title}".encode()).hexdigest()
        
        if any(j.get('job_hash') == job_hash for j in self.discovered_jobs):
            return False  # Duplicate
        
        job = {
            'job_hash': job_hash,
            'title': title,
            'company': company,
            'url': url,
            'source': source,
            'location': location,
            'salary': salary,
            'posted_date': posted_date,
            'discovered_date': datetime.now().isoformat(),
            'status': 'new',
            'notes': '',
            'relevance_score': self._calculate_relevance(title, description)
        }
        
        self.discovered_jobs.append(job)
        self._save_jobs()
        
        return True
    
    def _calculate_relevance(self, title: str, description: str) -> int:
        """
        Calculate job relevance score (0-100)
        
        Based on keyword matches and other factors
        """
        score = 50  # Base score
        
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Positive indicators
        positive_keywords = ['senior', 'lead', 'remote', 'competitive salary', 'benefits']
        for keyword in positive_keywords:
            if keyword in title_lower or keyword in desc_lower:
                score += 5
        
        # Negative indicators
        negative_keywords = ['unpaid', 'intern', 'entry level', 'junior']
        for keyword in negative_keywords:
            if keyword in title_lower:
                score -= 15
        
        return max(0, min(100, score))
    
    def get_new_jobs(self, min_relevance: int = 50) -> List[Dict]:
        """Get newly discovered jobs above relevance threshold"""
        return [job for job in self.discovered_jobs 
                if job['status'] == 'new' and 
                job['relevance_score'] >= min_relevance]
    
    def mark_job_status(self, job_hash: str, status: str):
        """
        Update job status
        
        Status: new, reviewed, applied, not_interested
        """
        for job in self.discovered_jobs:
            if job['job_hash'] == job_hash:
                job['status'] = status
                self._save_jobs()
                return
    
    def get_daily_digest(self) -> str:
        """Generate daily digest of new jobs"""
        new_jobs = self.get_new_jobs()
        
        if not new_jobs:
            return "No new jobs discovered today."
        
        digest = f"Daily Job Digest - {datetime.now().strftime('%Y-%m-%d')}\n"
        digest += "=" * 60 + "\n\n"
        digest += f"Found {len(new_jobs)} new relevant jobs:\n\n"
        
        # Sort by relevance
        new_jobs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        for i, job in enumerate(new_jobs[:10], 1):
            digest += f"{i}. {job['title']} at {job['company']}\n"
            digest += f"   Location: {job['location'] or 'Remote'}\n"
            digest += f"   Source: {job['source']}\n"
            digest += f"   Relevance: {job['relevance_score']}/100\n"
            digest += f"   URL: {job['url']}\n\n"
        
        if len(new_jobs) > 10:
            digest += f"... and {len(new_jobs) - 10} more jobs\n"
        
        return digest


class ApplicationTracker:
    """Track application materials and deadlines"""
    
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.deadlines_file = self.tracking_dir / "application_deadlines.json"
        self.deadlines = self._load_deadlines()
    
    def _load_deadlines(self) -> List[Dict]:
        if not self.deadlines_file.exists():
            return []
        
        with open(self.deadlines_file, 'r') as f:
            return json.load(f)
    
    def _save_deadlines(self):
        with open(self.deadlines_file, 'w') as f:
            json.dump(self.deadlines, f, indent=2)
    
    def add_deadline(self,
                    company: str,
                    position: str,
                    deadline: str,
                    materials_needed: List[str],
                    priority: str = "medium") -> str:
        """
        Track application deadline
        
        Args:
            company: Company name
            position: Position title
            deadline: Deadline date (YYYY-MM-DD)
            materials_needed: List of required materials
            priority: low, medium, high, critical
            
        Returns:
            Deadline ID
        """
        deadline_id = hashlib.md5(f"{company}{position}".encode()).hexdigest()[:8]
        
        deadline_entry = {
            'id': deadline_id,
            'company': company,
            'position': position,
            'deadline': deadline,
            'materials_needed': materials_needed,
            'materials_completed': [],
            'priority': priority,
            'status': 'pending',
            'created': datetime.now().isoformat()
        }
        
        self.deadlines.append(deadline_entry)
        self._save_deadlines()
        
        print(f"Deadline tracked: {company} - {position} (Due: {deadline})")
        return deadline_id
    
    def mark_material_complete(self, deadline_id: str, material: str):
        """Mark an application material as complete"""
        for deadline in self.deadlines:
            if deadline['id'] == deadline_id:
                if material not in deadline['materials_completed']:
                    deadline['materials_completed'].append(material)
                
                # Check if all materials complete
                if set(deadline['materials_completed']) >= set(deadline['materials_needed']):
                    deadline['status'] = 'ready'
                
                self._save_deadlines()
                print(f"✓ {material} completed for {deadline['company']}")
                return
    
    def get_upcoming_deadlines(self, days: int = 7) -> List[Dict]:
        """Get deadlines in the next N days"""
        today = datetime.now().date()
        cutoff = today + timedelta(days=days)
        
        upcoming = []
        for deadline in self.deadlines:
            if deadline['status'] == 'completed':
                continue
            
            deadline_date = datetime.fromisoformat(deadline['deadline']).date()
            if today <= deadline_date <= cutoff:
                days_remaining = (deadline_date - today).days
                upcoming.append({
                    **deadline,
                    'days_remaining': days_remaining
                })
        
        # Sort by days remaining
        upcoming.sort(key=lambda x: x['days_remaining'])
        return upcoming
    
    def get_deadline_summary(self) -> str:
        """Generate summary of upcoming deadlines"""
        upcoming = self.get_upcoming_deadlines(14)
        
        if not upcoming:
            return "No upcoming deadlines in the next 2 weeks."
        
        summary = "Application Deadlines Summary\n"
        summary += "=" * 60 + "\n\n"
        
        for deadline in upcoming:
            urgency = "🔴 URGENT" if deadline['days_remaining'] <= 2 else \
                     "🟡 SOON" if deadline['days_remaining'] <= 5 else "🟢 UPCOMING"
            
            summary += f"{urgency} - {deadline['company']}: {deadline['position']}\n"
            summary += f"  Due: {deadline['deadline']} ({deadline['days_remaining']} days)\n"
            summary += f"  Materials: {len(deadline['materials_completed'])}/{len(deadline['materials_needed'])} complete\n"
            
            incomplete = set(deadline['materials_needed']) - set(deadline['materials_completed'])
            if incomplete:
                summary += f"  Still need: {', '.join(incomplete)}\n"
            
            summary += "\n"
        
        return summary


def main():
    """Example usage"""
    print("Job Board Monitor & Alert System")
    print("=" * 60)
    
    # Initialize monitor
    monitor = JobBoardMonitor()
    tracker = ApplicationTracker()
    
    # Example: Add saved search
    print("\n1. Adding saved search...")
    search_id = monitor.add_search(
        name="Senior Python Developer - Remote",
        keywords=["senior python developer", "backend engineer"],
        location="",
        remote=True,
        min_salary=100000,
        experience_level="senior"
    )
    
    # Example: Generate search URLs
    print("\n2. Generated search URLs:")
    urls = monitor.generate_search_urls(search_id)
    for board, url in urls.items():
        print(f"  {board}: {url[:80]}...")
    
    # Example: Add discovered job
    print("\n3. Adding discovered job...")
    is_new = monitor.add_discovered_job(
        title="Senior Python Developer",
        company="Tech Corp",
        url="https://example.com/job/123",
        source="linkedin",
        location="Remote",
        salary="$120k-$150k",
        description="Looking for experienced Python developer..."
    )
    print(f"  New job: {is_new}")
    
    # Example: Daily digest
    print("\n4. Daily Digest:")
    print(monitor.get_daily_digest())
    
    # Example: Track deadline
    print("\n5. Tracking application deadline...")
    tracker.add_deadline(
        company="Dream Company",
        position="Lead Developer",
        deadline=(datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        materials_needed=["resume", "cover_letter", "portfolio", "references"],
        priority="high"
    )
    
    # Example: Deadline summary
    print("\n6. Deadline Summary:")
    print(tracker.get_deadline_summary())


if __name__ == "__main__":
    main()
