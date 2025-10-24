#!/usr/bin/env python3
"""
Enhanced LinkedIn Job Scraper
Scrapes public LinkedIn job listings without authentication
"""

import json
import argparse
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote_plus
import requests
from bs4 import BeautifulSoup

class LinkedInJobScraper:
    """Scrapes public LinkedIn job postings"""
    
    BASE_URL = "https://www.linkedin.com"
    JOBS_SEARCH_URL = f"{BASE_URL}/jobs/search"
    JOBS_API_URL = f"{BASE_URL}/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    def __init__(self, delay: float = 2.0):
        """
        Initialize scraper
        
        Args:
            delay: Delay between requests in seconds (be respectful!)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def search_jobs(self, 
                    keywords: str,
                    location: str = "",
                    job_type: Optional[str] = None,
                    experience_level: Optional[str] = None,
                    remote: bool = False,
                    max_results: int = 25) -> List[Dict]:
        """
        Search for jobs on LinkedIn
        
        Args:
            keywords: Job title or keywords
            location: Location (e.g., "New York, NY" or "Remote")
            job_type: F (Full-time), P (Part-time), C (Contract), T (Temporary), I (Internship)
            experience_level: 1 (Internship), 2 (Entry), 3 (Associate), 4 (Mid-Senior), 5 (Director), 6 (Executive)
            remote: Filter for remote jobs
            max_results: Maximum number of results to return
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Build search parameters
        params = {
            'keywords': keywords,
            'location': location,
            'start': 0
        }
        
        if job_type:
            params['f_JT'] = job_type
        
        if experience_level:
            params['f_E'] = experience_level
        
        if remote:
            params['f_WT'] = '2'  # Remote filter
        
        print(f"🔍 Searching LinkedIn jobs: {keywords} in {location or 'Any location'}")
        print(f"   Remote: {remote}, Max results: {max_results}")
        
        page = 0
        while len(jobs) < max_results:
            params['start'] = page * 25
            
            try:
                # Use the guest API endpoint (doesn't require auth)
                url = f"{self.JOBS_API_URL}?{urlencode(params)}"
                print(f"   Fetching page {page + 1}...")
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='base-card')
                
                if not job_cards:
                    print(f"   No more jobs found on page {page + 1}")
                    break
                
                for card in job_cards:
                    if len(jobs) >= max_results:
                        break
                    
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                        print(f"   ✓ {job['title']} at {job['company']}")
                
                page += 1
                
                # Be respectful - add delay between requests
                if len(jobs) < max_results and job_cards:
                    time.sleep(self.delay)
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ Error fetching page {page + 1}: {e}")
                break
        
        print(f"✅ Found {len(jobs)} jobs")
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a job card from LinkedIn search results"""
        try:
            # Extract job ID and URL
            job_link = card.find('a', class_='base-card__full-link')
            if not job_link:
                return None
            
            job_url = job_link.get('href', '')
            job_id = self._extract_job_id(job_url)
            
            # Extract title
            title_elem = card.find('h3', class_='base-search-card__title')
            title = title_elem.text.strip() if title_elem else 'Unknown Title'
            
            # Extract company
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            company = company_elem.text.strip() if company_elem else 'Unknown Company'
            
            # Extract location
            location_elem = card.find('span', class_='job-search-card__location')
            location = location_elem.text.strip() if location_elem else 'Unknown Location'
            
            # Extract posted date
            time_elem = card.find('time')
            posted_date = time_elem.get('datetime', '') if time_elem else ''
            
            # Extract salary if available
            salary_elem = card.find('span', class_='job-search-card__salary-info')
            salary = salary_elem.text.strip() if salary_elem else None
            
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'url': job_url,
                'posted_date': posted_date,
                'scraped_at': datetime.now().isoformat(),
                'source': 'linkedin'
            }
            
        except Exception as e:
            print(f"   ⚠️ Error parsing job card: {e}")
            return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """
        Get detailed information about a specific job
        
        Args:
            job_url: Full LinkedIn job URL
            
        Returns:
            Job details dictionary
        """
        try:
            print(f"📄 Fetching job details: {job_url}")
            
            # Extract job ID from URL
            job_id = self._extract_job_id(job_url)
            
            # Use guest view endpoint
            guest_url = f"{self.BASE_URL}/jobs-guest/jobs/api/jobPosting/{job_id}"
            
            response = self.session.get(guest_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract detailed information
            job = {
                'id': job_id,
                'url': job_url,
                'scraped_at': datetime.now().isoformat(),
                'source': 'linkedin'
            }
            
            # Title
            title_elem = soup.find('h2', class_='top-card-layout__title')
            job['title'] = title_elem.text.strip() if title_elem else 'Unknown Title'
            
            # Company
            company_elem = soup.find('a', class_='topcard__org-name-link')
            if not company_elem:
                company_elem = soup.find('span', class_='topcard__flavor')
            job['company'] = company_elem.text.strip() if company_elem else 'Unknown Company'
            
            # Location
            location_elem = soup.find('span', class_='topcard__flavor--bullet')
            job['location'] = location_elem.text.strip() if location_elem else 'Unknown Location'
            
            # Job description
            desc_elem = soup.find('div', class_='show-more-less-html__markup')
            if desc_elem:
                job['description'] = desc_elem.get_text(separator='\n', strip=True)
            else:
                job['description'] = ''
            
            # Job criteria (employment type, seniority, etc.)
            criteria_list = soup.find_all('li', class_='description__job-criteria-item')
            criteria = {}
            for item in criteria_list:
                header = item.find('h3')
                value = item.find('span')
                if header and value:
                    criteria[header.text.strip()] = value.text.strip()
            
            job['employment_type'] = criteria.get('Employment type', '')
            job['seniority_level'] = criteria.get('Seniority level', '')
            job['job_function'] = criteria.get('Job function', '')
            job['industries'] = criteria.get('Industries', '')
            
            # Extract skills if available
            skills = []
            skills_section = soup.find('div', class_='skills-section')
            if skills_section:
                skill_items = skills_section.find_all('span', class_='skill-name')
                skills = [s.text.strip() for s in skill_items]
            job['skills'] = skills
            
            # Extract applicant count
            applicant_elem = soup.find('span', class_='num-applicants__caption')
            if applicant_elem:
                job['applicants'] = applicant_elem.text.strip()
            
            print(f"   ✓ {job['title']} at {job['company']}")
            
            return job
            
        except Exception as e:
            print(f"   ⚠️ Error fetching job details: {e}")
            return None
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from LinkedIn URL"""
        match = re.search(r'/(\d+)/?', url)
        return match.group(1) if match else url.split('/')[-1]
    
    def scrape_from_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape jobs from a list of LinkedIn job URLs
        
        Args:
            urls: List of LinkedIn job URLs
            
        Returns:
            List of job details
        """
        jobs = []
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Processing: {url}")
            job = self.get_job_details(url)
            
            if job:
                jobs.append(job)
            
            # Be respectful - delay between requests
            if i < len(urls):
                time.sleep(self.delay)
        
        print(f"✅ Scraped {len(jobs)} jobs from URLs")
        return jobs


def main():
    parser = argparse.ArgumentParser(
        description='LinkedIn Job Scraper - Extract public job listings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for data science jobs
  python linkedin_job_scraper.py --keywords "data scientist" --location "San Francisco, CA"
  
  # Search for remote software engineering jobs
  python linkedin_job_scraper.py --keywords "software engineer" --remote --max-results 50
  
  # Get details from specific job URLs
  python linkedin_job_scraper.py --mode urls --urls jobs.txt
  
  # Search with filters
  python linkedin_job_scraper.py --keywords "product manager" --experience-level 4 --job-type F
        """
    )
    
    parser.add_argument('--mode', choices=['search', 'urls'], default='search',
                       help='Scraping mode: search LinkedIn or scrape from URLs')
    
    # Search mode arguments
    parser.add_argument('--keywords', default='',
                       help='Job keywords or title (e.g., "data scientist")')
    parser.add_argument('--location', default='',
                       help='Job location (e.g., "New York, NY")')
    parser.add_argument('--remote', action='store_true',
                       help='Filter for remote jobs only')
    parser.add_argument('--job-type',
                       help='Job type: F (Full-time), P (Part-time), C (Contract), T (Temporary), I (Internship)')
    parser.add_argument('--experience-level',
                       help='Experience level: 1 (Internship), 2 (Entry), 3 (Associate), 4 (Mid-Senior), 5 (Director), 6 (Executive)')
    parser.add_argument('--max-results', type=int, default=25,
                       help='Maximum number of results (default: 25)')
    
    # URL mode arguments
    parser.add_argument('--urls', 
                       help='File containing LinkedIn job URLs (one per line)')
    parser.add_argument('--url',
                       help='Single LinkedIn job URL to scrape')
    
    # Output arguments
    parser.add_argument('--output', default='linkedin_jobs.json',
                       help='Output JSON file (default: linkedin_jobs.json)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between requests in seconds (default: 2.0)')
    parser.add_argument('--append', action='store_true',
                       help='Append to existing output file')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = LinkedInJobScraper(delay=args.delay)
    jobs = []
    
    try:
        if args.mode == 'search':
            # Search mode
            if not args.keywords:
                print("❌ Error: --keywords required for search mode")
                return
            
            jobs = scraper.search_jobs(
                keywords=args.keywords,
                location=args.location,
                job_type=args.job_type,
                experience_level=args.experience_level,
                remote=args.remote,
                max_results=args.max_results
            )
            
        elif args.mode == 'urls':
            # URL scraping mode
            urls = []
            
            if args.url:
                # Single URL
                urls = [args.url]
            elif args.urls:
                # Read URLs from file
                try:
                    with open(args.urls, 'r') as f:
                        urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
                except FileNotFoundError:
                    print(f"❌ Error: File not found: {args.urls}")
                    return
            else:
                print("❌ Error: --url or --urls required for urls mode")
                return
            
            if urls:
                print(f"📋 Found {len(urls)} URLs to scrape")
                jobs = scraper.scrape_from_urls(urls)
        
        # Load existing jobs if appending
        existing_jobs = []
        if args.append:
            try:
                with open(args.output, 'r') as f:
                    existing_jobs = json.load(f)
                print(f"📂 Loaded {len(existing_jobs)} existing jobs")
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        
        # Combine and deduplicate
        all_jobs = existing_jobs + jobs
        unique_jobs = {job['id']: job for job in all_jobs if 'id' in job}
        final_jobs = list(unique_jobs.values())
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(final_jobs, f, indent=2)
        
        print(f"\n✅ Saved {len(final_jobs)} jobs to {args.output}")
        
        # Print summary
        if jobs:
            print("\n📊 Summary:")
            print(f"   New jobs scraped: {len(jobs)}")
            print(f"   Total jobs in file: {len(final_jobs)}")
            
            # Count by company
            companies = {}
            for job in jobs:
                company = job.get('company', 'Unknown')
                companies[company] = companies.get(company, 0) + 1
            
            print(f"\n🏢 Top companies:")
            for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {company}: {count} jobs")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        if jobs:
            # Save partial results
            with open(args.output, 'w') as f:
                json.dump(jobs, f, indent=2)
            print(f"💾 Saved {len(jobs)} partial results to {args.output}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
