#!/usr/bin/env python3
"""
Enhanced Indeed Job Scraper
Advanced web scraping with retry logic, rate limiting, and comprehensive data extraction
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus
import logging
from typing import List, Dict, Optional, Set
import re
from dataclasses import dataclass, asdict
from functools import wraps
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('indeed_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class JobListing:
    """Structured job listing data"""
    id: str
    title: str
    company: str
    location: str
    salary: str
    description_snippet: str
    url: str
    posted_date: str
    job_type: str
    remote_option: bool
    attributes: List[str]
    source: str
    scraped_at: str
    full_description: Optional[str] = None
    requirements: Optional[List[str]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    """Decorator for retrying failed requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {str(e)}")
                        raise
                    wait_time = delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter for API requests"""
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = 0
    
    def wait(self):
        """Wait if necessary to respect rate limit"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_request = time.time()


class IndeedScraper:
    """Enhanced Indeed UK job scraper with advanced features"""
    
    BASE_URL = "https://uk.indeed.com"
    
    def __init__(self, headless: bool = True, requests_per_minute: int = 30):
        self.session = self._create_session()
        self.jobs: List[JobListing] = []
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.seen_job_ids: Set[str] = set()
        
    def _create_session(self) -> requests.Session:
        """Create configured requests session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        return session
    
    @retry_on_failure(max_retries=3)
    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with retry logic"""
        self.rate_limiter.wait()
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return response
    
    def search_jobs(self, 
                   job_title: str, 
                   location: str = "London", 
                   max_results: int = 100,
                   job_type: Optional[str] = None,
                   salary_min: Optional[int] = None,
                   remote_only: bool = False,
                   posted_days: Optional[int] = None,
                   radius: int = 25) -> List[JobListing]:
        """
        Search for jobs on Indeed with advanced filtering
        
        Args:
            job_title: Job title or keywords
            location: Location (default: London)
            max_results: Maximum number of results
            job_type: fulltime, contract, temporary, parttime, internship
            salary_min: Minimum salary (annual)
            remote_only: Filter for remote jobs only
            posted_days: Jobs posted within last N days
            radius: Search radius in miles
        
        Returns:
            List of JobListing objects
        """
        logger.info(f"🔍 Searching Indeed for: '{job_title}' in '{location}'")
        logger.info(f"Filters: type={job_type}, salary_min={salary_min}, remote={remote_only}")
        
        start = 0
        page = 0
        consecutive_empty_pages = 0
        max_empty_pages = 3
        
        while len(self.jobs) < max_results and consecutive_empty_pages < max_empty_pages:
            params = self._build_search_params(
                job_title, location, start, job_type, 
                salary_min, remote_only, posted_days, radius
            )
            
            url = f"{self.BASE_URL}/jobs?{urlencode(params)}"
            
            try:
                response = self._make_request(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors for job cards
                job_cards = self._find_job_cards(soup)
                
                if not job_cards:
                    consecutive_empty_pages += 1
                    logger.warning(f"No jobs found on page {page + 1}")
                    if consecutive_empty_pages >= max_empty_pages:
                        logger.info("Multiple empty pages, ending search")
                        break
                    start += 10
                    page += 1
                    continue
                
                consecutive_empty_pages = 0
                jobs_added = 0
                
                for card in job_cards:
                    if len(self.jobs) >= max_results:
                        break
                    
                    job_data = self._parse_job_card(card)
                    if job_data and job_data.id not in self.seen_job_ids:
                        self.jobs.append(job_data)
                        self.seen_job_ids.add(job_data.id)
                        jobs_added += 1
                
                logger.info(f"Page {page + 1}: Found {len(job_cards)} cards, Added {jobs_added} new jobs | Total: {len(self.jobs)}")
                
                page += 1
                start += 10
                
                # Random delay to appear more human-like
                time.sleep(random.uniform(1.5, 3.5))
                
            except requests.RequestException as e:
                logger.error(f"Request failed on page {page}: {str(e)}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_empty_pages:
                    break
            except Exception as e:
                logger.error(f"Unexpected error on page {page}: {str(e)}", exc_info=True)
                break
        
        logger.info(f"✅ Scraping complete: {len(self.jobs)} unique jobs found")
        return self.jobs
    
    def _build_search_params(self, job_title: str, location: str, start: int,
                            job_type: Optional[str], salary_min: Optional[int],
                            remote_only: bool, posted_days: Optional[int],
                            radius: int) -> Dict:
        """Build search parameters"""
        params = {
            'q': job_title,
            'l': location,
            'start': start,
            'radius': radius,
            'sort': 'date'  # Sort by most recent
        }
        
        if job_type:
            params['jt'] = job_type
        
        if salary_min:
            params['salary'] = str(salary_min)
        
        if remote_only:
            params['remotejob'] = '1'
        
        if posted_days:
            params['fromage'] = str(posted_days)
        
        return params
    
    def _find_job_cards(self, soup: BeautifulSoup) -> List:
        """Find job cards using multiple selectors"""
        # Try multiple selectors as Indeed's HTML structure varies
        selectors = [
            ('div', {'class': 'job_seen_beacon'}),
            ('div', {'class': 'jobsearch-SerpJobCard'}),
            ('div', {'data-testid': 'job-result'}),
            ('article', {'class': 'job_seen_beacon'}),
        ]
        
        for tag, attrs in selectors:
            cards = soup.find_all(tag, attrs)
            if cards:
                return cards
        
        return []
    
    def _parse_job_card(self, card) -> Optional[JobListing]:
        """Parse individual job card with comprehensive data extraction"""
        try:
            # Job title and link
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                title_elem = card.find('a', {'data-jk': True})
            
            if not title_elem:
                return None
            
            title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
            job_title = self._clean_text(title_link.get_text() if title_link else title_elem.get_text())
            
            job_id = title_link.get('data-jk', '') if title_link else card.get('data-jk', '')
            if not job_id:
                # Try to extract from ID attribute
                card_id = card.get('id', '')
                if card_id:
                    job_id = card_id.replace('job_', '')
            
            job_url = f"{self.BASE_URL}/viewjob?jk={job_id}" if job_id else ""
            
            # Company name
            company_elem = card.find('span', {'data-testid': 'company-name'})
            if not company_elem:
                company_elem = card.find('span', class_='companyName')
            company = self._clean_text(company_elem.get_text() if company_elem else "Unknown")
            
            # Location
            location_elem = card.find('div', {'data-testid': 'text-location'})
            if not location_elem:
                location_elem = card.find('div', class_='companyLocation')
            location = self._clean_text(location_elem.get_text() if location_elem else "")
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet')
            if not salary_elem:
                salary_elem = card.find('span', class_='salary-snippet')
            salary_text = self._clean_text(salary_elem.get_text() if salary_elem else "")
            
            # Parse salary range
            salary_min, salary_max, currency = self._parse_salary(salary_text)
            
            # Job snippet/description
            snippet_elem = card.find('div', class_='job-snippet')
            if not snippet_elem:
                snippet_elem = card.find('div', {'data-testid': 'job-snippet'})
            snippet = self._clean_text(snippet_elem.get_text() if snippet_elem else "")
            
            # Job attributes (full-time, remote, etc.)
            attributes = []
            attr_elems = card.find_all('div', class_='attribute_snippet')
            if not attr_elems:
                attr_elems = card.find_all('span', class_='attribute_snippet')
            
            for attr in attr_elems:
                attr_text = self._clean_text(attr.get_text())
                if attr_text:
                    attributes.append(attr_text)
            
            # Check for remote
            remote_option = any('remote' in attr.lower() for attr in attributes) or 'remote' in snippet.lower()
            
            # Job type
            job_type = self._extract_job_type(attributes, snippet)
            
            # Post date
            date_elem = card.find('span', class_='date')
            if not date_elem:
                date_elem = card.find('span', {'data-testid': 'myJobsStateDate'})
            posted_date = self._clean_text(date_elem.get_text() if date_elem else "")
            
            return JobListing(
                id=job_id,
                title=job_title,
                company=company,
                location=location,
                salary=salary_text,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                description_snippet=snippet,
                url=job_url,
                posted_date=posted_date,
                job_type=job_type,
                remote_option=remote_option,
                attributes=attributes,
                source='indeed',
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.debug(f"Error parsing job card: {str(e)}")
            return None
    
    def _parse_salary(self, salary_text: str) -> tuple[Optional[float], Optional[float], Optional[str]]:
        """Parse salary text into min, max, and currency"""
        if not salary_text:
            return None, None, None
        
        # Extract currency
        currency = 'GBP' if '£' in salary_text else 'USD' if '$' in salary_text else None
        
        # Remove currency symbols and clean
        cleaned = re.sub(r'[£$,]', '', salary_text)
        
        # Try to find salary range
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)', cleaned)
        if range_match:
            min_sal = float(range_match.group(1))
            max_sal = float(range_match.group(2))
            # Convert to annual if needed
            if 'hour' in salary_text.lower():
                min_sal *= 2080  # ~40 hours/week * 52 weeks
                max_sal *= 2080
            return min_sal, max_sal, currency
        
        # Single salary value
        single_match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
        if single_match:
            salary = float(single_match.group(1))
            if 'hour' in salary_text.lower():
                salary *= 2080
            # If it's a single value, use it for both min and max
            return salary, salary, currency
        
        return None, None, currency
    
    def _extract_job_type(self, attributes: List[str], snippet: str) -> str:
        """Extract job type from attributes and snippet"""
        text = ' '.join(attributes + [snippet]).lower()
        
        if 'full-time' in text or 'full time' in text:
            return 'fulltime'
        elif 'part-time' in text or 'part time' in text:
            return 'parttime'
        elif 'contract' in text:
            return 'contract'
        elif 'temporary' in text or 'temp' in text:
            return 'temporary'
        elif 'internship' in text or 'intern' in text:
            return 'internship'
        
        return 'unknown'
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @retry_on_failure(max_retries=2)
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Fetch full job details including requirements"""
        url = f"{self.BASE_URL}/viewjob?jk={job_id}"
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Full job description
            desc_elem = soup.find('div', id='jobDescriptionText')
            if desc_elem:
                details['full_description'] = self._clean_text(desc_elem.get_text('\n'))
                
                # Extract requirements
                requirements = self._extract_requirements(desc_elem)
                if requirements:
                    details['requirements'] = requirements
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching job details for {job_id}: {str(e)}")
            return None
    
    def _extract_requirements(self, description_elem) -> List[str]:
        """Extract requirements from job description"""
        requirements = []
        text = description_elem.get_text().lower()
        
        # Look for requirements sections
        req_patterns = [
            r'requirements?:(.+?)(?:responsibilities|qualifications|about|$)',
            r'qualifications?:(.+?)(?:responsibilities|requirements|about|$)',
            r'must have:(.+?)(?:nice to have|responsibilities|about|$)'
        ]
        
        for pattern in req_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                req_text = match.group(1)
                # Extract bullet points or lines
                lines = [line.strip() for line in req_text.split('\n') if line.strip()]
                requirements.extend(lines[:10])  # Limit to 10 requirements
                break
        
        return requirements
    
    def enrich_jobs_with_details(self, max_jobs: int = 20):
        """Fetch full details for top jobs"""
        logger.info(f"📝 Enriching top {min(max_jobs, len(self.jobs))} jobs with full details...")
        
        for i, job in enumerate(self.jobs[:max_jobs]):
            if not job.id:
                continue
                
            logger.info(f"Fetching details {i+1}/{min(max_jobs, len(self.jobs))}: {job.title} at {job.company}")
            details = self.get_job_details(job.id)
            
            if details:
                job.full_description = details.get('full_description')
                job.requirements = details.get('requirements')
            
            time.sleep(random.uniform(1, 2.5))
    
    def save_jobs(self, filename: str = 'indeed_jobs.json', format: str = 'json'):
        """Save scraped jobs to file"""
        output_path = Path(filename)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                jobs_dict = [asdict(job) for job in self.jobs]
                json.dump(jobs_dict, f, indent=2, ensure_ascii=False)
        elif format == 'csv':
            import csv
            with open(output_path.with_suffix('.csv'), 'w', encoding='utf-8', newline='') as f:
                if self.jobs:
                    writer = csv.DictWriter(f, fieldnames=asdict(self.jobs[0]).keys())
                    writer.writeheader()
                    for job in self.jobs:
                        writer.writerow(asdict(job))
        
        logger.info(f"💾 Saved {len(self.jobs)} jobs to {output_path}")
    
    def get_statistics(self) -> Dict:
        """Get statistics about scraped jobs"""
        if not self.jobs:
            return {}
        
        stats = {
            'total_jobs': len(self.jobs),
            'unique_companies': len(set(j.company for j in self.jobs)),
            'unique_locations': len(set(j.location for j in self.jobs)),
            'with_salary': sum(1 for j in self.jobs if j.salary),
            'remote_jobs': sum(1 for j in self.jobs if j.remote_option),
            'job_types': {}
        }
        
        # Job type distribution
        for job in self.jobs:
            jt = job.job_type
            stats['job_types'][jt] = stats['job_types'].get(jt, 0) + 1
        
        # Salary statistics
        salaries = [j.salary_min for j in self.jobs if j.salary_min]
        if salaries:
            stats['avg_salary'] = sum(salaries) / len(salaries)
            stats['min_salary'] = min(salaries)
            stats['max_salary'] = max(salaries)
        
        return stats
    
    def print_summary(self):
        """Print comprehensive scraping summary"""
        stats = self.get_statistics()
        
        if not stats:
            print("\n⚠️ No jobs to summarize")
            return
        
        print("\n" + "="*70)
        print("📊 INDEED SCRAPING SUMMARY")
        print("="*70)
        print(f"Total Jobs:           {stats['total_jobs']}")
        print(f"Unique Companies:     {stats['unique_companies']}")
        print(f"Unique Locations:     {stats['unique_locations']}")
        print(f"With Salary Info:     {stats['with_salary']} ({stats['with_salary']/stats['total_jobs']*100:.1f}%)")
        print(f"Remote Jobs:          {stats['remote_jobs']} ({stats['remote_jobs']/stats['total_jobs']*100:.1f}%)")
        
        if 'avg_salary' in stats:
            print(f"\nSalary Statistics:")
            print(f"  Average:  £{stats['avg_salary']:,.0f}")
            print(f"  Range:    £{stats['min_salary']:,.0f} - £{stats['max_salary']:,.0f}")
        
        print(f"\nJob Types:")
        for jt, count in sorted(stats['job_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {jt.capitalize():15} {count:3d} ({count/stats['total_jobs']*100:5.1f}%)")
        
        print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Indeed Job Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --keywords "Software Engineer" --location London --max 100
  %(prog)s -k "Data Scientist" -l Manchester --salary-min 50000 --remote
  %(prog)s -k "DevOps" -l "United Kingdom" --job-type fulltime --enrich 10
        """
    )
    
    parser.add_argument('--keywords', '-k', required=True, help='Job keywords/title')
    parser.add_argument('--location', '-l', default='London', help='Location (default: London)')
    parser.add_argument('--max-results', '--max', '-m', type=int, default=50, 
                       help='Max results (default: 50)')
    parser.add_argument('--job-type', '-j', choices=['fulltime', 'contract', 'temporary', 'parttime', 'internship'],
                       help='Job type filter')
    parser.add_argument('--salary-min', '-s', type=int, help='Minimum annual salary')
    parser.add_argument('--remote', '-r', action='store_true', help='Remote jobs only')
    parser.add_argument('--posted-days', '-p', type=int, choices=[1, 3, 7, 14, 30],
                       help='Jobs posted within last N days')
    parser.add_argument('--radius', type=int, default=25, help='Search radius in miles (default: 25)')
    parser.add_argument('--enrich', '-e', type=int, default=0, 
                       help='Enrich top N jobs with full details (default: 0)')
    parser.add_argument('--output', '-o', default='indeed_jobs.json', help='Output filename')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--rate-limit', type=int, default=30,
                       help='Requests per minute (default: 30)')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = IndeedScraper(requests_per_minute=args.rate_limit)
    
    # Search jobs
    jobs = scraper.search_jobs(
        job_title=args.keywords,
        location=args.location,
        max_results=args.max_results,
        job_type=args.job_type,
        salary_min=args.salary_min,
        remote_only=args.remote,
        posted_days=args.posted_days,
        radius=args.radius
    )
    
    if not jobs:
        logger.warning("No jobs found. Try adjusting your search parameters.")
        return
    
    # Enrich with full details
    if args.enrich > 0:
        scraper.enrich_jobs_with_details(args.enrich)
    
    # Save results
    scraper.save_jobs(args.output, args.format)
    
    # Print summary
    scraper.print_summary()
    
    print(f"\n✅ Scraping complete! {len(jobs)} jobs saved to {args.output}")


if __name__ == "__main__":
    main()
