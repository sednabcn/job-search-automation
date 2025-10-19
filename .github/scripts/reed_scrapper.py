#!/usr/bin/env python3
"""
Reed.co.uk Job Scraper - Enhanced Version
Comprehensive scraping with both web and API support
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from urllib.parse import quote_plus, urljoin
import logging
from typing import List, Dict, Optional
import re
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReedScraper:
    """Enhanced Reed.co.uk job scraper with API and web scraping"""
    
    BASE_URL = "https://www.reed.co.uk"
    API_URL = "https://www.reed.co.uk/api/1.0/search"
    
    def __init__(self, api_key: Optional[str] = None, headless: bool = True):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.jobs = []
    
    def search_jobs(self, 
                   job_title: str, 
                   location: str = "London", 
                   max_results: int = 100,
                   distance: int = 10,
                   salary_min: Optional[int] = None,
                   contract_type: Optional[str] = None,
                   posted_days: Optional[int] = None) -> List[Dict]:
        """
        Web scraping method for Reed jobs
        
        Args:
            job_title: Job title or keywords
            location: Location to search
            max_results: Maximum number of results
            distance: Search radius in miles
            salary_min: Minimum salary
            contract_type: permanent, contract, temp, parttime
            posted_days: Jobs posted within X days (7, 14, 30)
        """
        logger.info(f"🔍 Scraping Reed for: {job_title} in {location}")
        
        page = 1
        jobs_found = 0
        
        while jobs_found < max_results:
            try:
                # Build search URL
                url = self._build_search_url(
                    job_title, location, page, 
                    distance, salary_min, contract_type, posted_days
                )
                
                logger.info(f"Fetching page {page}...")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards - Reed uses different selectors
                job_cards = soup.find_all('article', class_='job-result')
                if not job_cards:
                    # Try alternative selector
                    job_cards = soup.find_all('div', {'data-qa': 'job-card'})
                
                if not job_cards:
                    logger.info("No more jobs found")
                    break
                
                for card in job_cards:
                    if jobs_found >= max_results:
                        break
                    
                    job_data = self._parse_job_card(card)
                    if job_data:
                        self.jobs.append(job_data)
                        jobs_found += 1
                
                logger.info(f"Page {page}: Found {len(job_cards)} jobs | Total: {jobs_found}")
                
                # Check for next page
                pagination = soup.find('div', class_='pagination')
                if not pagination or not self._has_next_page(soup):
                    logger.info("No more pages available")
                    break
                
                page += 1
                time.sleep(random.uniform(2, 5))
                
            except requests.RequestException as e:
                logger.error(f"Request failed on page {page}: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Error on page {page}: {str(e)}")
                break
        
        logger.info(f"✅ Total jobs scraped: {len(self.jobs)}")
        return self.jobs
    
    def _build_search_url(self, job_title: str, location: str, page: int,
                         distance: int, salary_min: Optional[int],
                         contract_type: Optional[str], posted_days: Optional[int]) -> str:
        """Build Reed search URL"""
        keywords = quote_plus(job_title)
        loc = quote_plus(location)
        
        # Base URL structure
        url = f"{self.BASE_URL}/jobs/{keywords}-jobs-in-{loc}?pageno={page}"
        
        # Add filters
        params = []
        if distance:
            params.append(f"proximity={distance}")
        if salary_min:
            params.append(f"salaryfrom={salary_min}")
        if contract_type:
            params.append(f"contracttype={contract_type}")
        if posted_days:
            params.append(f"datecreatedoffset={posted_days}")
        
        if params:
            url += "&" + "&".join(params)
        
        return url
    
    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page"""
        next_button = soup.find('a', {'aria-label': 'Next page'})
        if not next_button:
            next_button = soup.find('a', string=re.compile(r'Next', re.I))
        return next_button is not None
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse individual Reed job card"""
        try:
            # Job title and URL
            title_elem = card.find('h2', class_='job-result-heading__title')
            if not title_elem:
                title_elem = card.find('a', {'data-qa': 'job-card-title'})
            
            if not title_elem:
                return None
            
            title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
            job_title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
            
            job_url = ""
            if title_link and title_link.get('href'):
                job_url = urljoin(self.BASE_URL, title_link['href'])
            
            # Extract job ID from URL
            job_id = ""
            if job_url:
                match = re.search(r'/(\d+)(?:\?|$)', job_url)
                if match:
                    job_id = match.group(1)
            
            # Company name
            company_elem = card.find('a', class_='gtmJobListingPostedBy')
            if not company_elem:
                company_elem = card.find('a', {'data-qa': 'job-card-company'})
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find('li', class_='job-metadata__item--location')
            if not location_elem:
                location_elem = card.find('span', {'data-qa': 'job-card-location'})
            location = location_elem.get_text(strip=True).replace('Location', '').strip() if location_elem else ""
            
            # Salary
            salary_elem = card.find('li', class_='job-metadata__item--salary')
            if not salary_elem:
                salary_elem = card.find('span', {'data-qa': 'job-card-salary'})
            salary = salary_elem.get_text(strip=True).replace('Salary', '').strip() if salary_elem else ""
            
            # Contract type
            contract_elem = card.find('li', class_='job-metadata__item--type')
            if not contract_elem:
                contract_elem = card.find('span', {'data-qa': 'job-card-type'})
            contract_type = contract_elem.get_text(strip=True) if contract_elem else ""
            
            # Job description snippet
            desc_elem = card.find('p', class_='job-result-description__details')
            if not desc_elem:
                desc_elem = card.find('div', {'data-qa': 'job-card-description'})
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Posted date
            date_elem = card.find('li', class_='job-metadata__item--date')
            if not date_elem:
                date_elem = card.find('span', {'data-qa': 'job-card-date'})
            posted_date = date_elem.get_text(strip=True).replace('Posted', '').strip() if date_elem else ""
            
            job_data = {
                'id': job_id,
                'title': job_title,
                'company': company,
                'location': location,
                'salary': salary,
                'contract_type': contract_type,
                'description_snippet': description,
                'url': job_url,
                'posted_date': posted_date,
                'source': 'reed',
                'scraped_at': datetime.now().isoformat()
            }
            
            return job_data
            
        except Exception as e:
            logger.debug(f"Error parsing job card: {str(e)}")
            return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Fetch full job details from job page"""
        try:
            logger.debug(f"Fetching job details: {job_url}")
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Full job description
            desc_elem = soup.find('div', itemprop='description')
            if not desc_elem:
                desc_elem = soup.find('span', itemprop='description')
            if desc_elem:
                details['full_description'] = desc_elem.get_text('\n', strip=True)
            
            # Job requirements
            requirements = []
            req_section = soup.find('div', class_='skills')
            if req_section:
                req_items = req_section.find_all('li')
                requirements = [item.get_text(strip=True) for item in req_items]
                details['requirements'] = requirements
            
            # Benefits
            benefits = []
            benefits_section = soup.find('div', class_='benefits')
            if benefits_section:
                benefit_items = benefits_section.find_all('li')
                benefits = [item.get_text(strip=True) for item in benefit_items]
                details['benefits'] = benefits
            
            # Additional salary info
            salary_detail = soup.find('span', itemprop='baseSalary')
            if salary_detail:
                details['salary_detail'] = salary_detail.get_text(strip=True)
            
            # Employment type
            emp_type = soup.find('span', itemprop='employmentType')
            if emp_type:
                details['employment_type'] = emp_type.get_text(strip=True)
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching job details: {str(e)}")
            return None
    
    def search_with_api(self, 
                       keywords: str,
                       location: str = "London",
                       max_results: int = 100,
                       distance: int = 10,
                       salary_min: Optional[int] = None) -> List[Dict]:
        """
        Search using Reed API (requires API key)
        Get your API key from: https://www.reed.co.uk/developers/jobseeker
        """
        if not self.api_key:
            logger.error("❌ API key required. Get one from: https://www.reed.co.uk/developers/jobseeker")
            return []
        
        logger.info(f"🔍 Searching Reed API for: {keywords} in {location}")
        
        all_results = []
        results_per_page = 100
        
        for skip in range(0, max_results, results_per_page):
            params = {
                'keywords': keywords,
                'locationName': location,
                'distanceFromLocation': distance,
                'resultsToTake': min(results_per_page, max_results - skip),
                'resultsToSkip': skip
            }
            
            if salary_min:
                params['minimumSalary'] = salary_min
            
            try:
                response = requests.get(
                    self.API_URL,
                    params=params,
                    auth=(self.api_key, ''),
                    timeout=15
                )
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.info("No more results from API")
                    break
                
                for job in results:
                    job_data = {
                        'id': str(job.get('jobId', '')),
                        'title': job.get('jobTitle', ''),
                        'company': job.get('employerName', ''),
                        'location': job.get('locationName', ''),
                        'salary': self._format_salary(job.get('minimumSalary'), job.get('maximumSalary')),
                        'salary_min': job.get('minimumSalary'),
                        'salary_max': job.get('maximumSalary'),
                        'description_snippet': job.get('jobDescription', ''),
                        'full_description': job.get('jobDescription', ''),
                        'url': job.get('jobUrl', ''),
                        'posted_date': job.get('date', ''),
                        'contract_type': job.get('contractType', ''),
                        'expiration_date': job.get('expirationDate', ''),
                        'source': 'reed_api',
                        'scraped_at': datetime.now().isoformat()
                    }
                    all_results.append(job_data)
                
                logger.info(f"Fetched {len(results)} jobs via API | Total: {len(all_results)}")
                time.sleep(0.5)
                
            except requests.RequestException as e:
                logger.error(f"API request failed: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Error processing API response: {str(e)}")
                break
        
        logger.info(f"✅ Total jobs from API: {len(all_results)}")
        return all_results
    
    def _format_salary(self, min_sal, max_sal) -> str:
        """Format salary range"""
        if not min_sal and not max_sal:
            return ""
        if min_sal and max_sal:
            return f"£{min_sal:,} - £{max_sal:,}"
        if min_sal:
            return f"£{min_sal:,}+"
        return f"Up to £{max_sal:,}"
    
    def enrich_jobs_with_details(self, max_jobs: int = 10):
        """Fetch full details for top jobs"""
        logger.info(f"Enriching {min(max_jobs, len(self.jobs))} jobs with full details...")
        
        for i, job in enumerate(self.jobs[:max_jobs]):
            if job.get('url'):
                logger.info(f"Fetching details {i+1}/{min(max_jobs, len(self.jobs))}: {job['title']}")
                details = self.get_job_details(job['url'])
                if details:
                    job.update(details)
                time.sleep(random.uniform(1, 3))
    
    def save_jobs(self, filename: str = 'reed_jobs.json'):
        """Save scraped jobs to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved {len(self.jobs)} jobs to {filename}")
    
    def print_summary(self):
        """Print scraping summary"""
        if not self.jobs:
            logger.warning("No jobs to summarize")
            return
        
        print("\n" + "="*60)
        print("📊 REED SCRAPING SUMMARY")
        print("="*60)
        print(f"Total Jobs: {len(self.jobs)}")
        print(f"Unique Companies: {len(set(j['company'] for j in self.jobs))}")
        print(f"Locations: {len(set(j['location'] for j in self.jobs))}")
        
        with_salary = sum(1 for j in self.jobs if j.get('salary'))
        print(f"With Salary Info: {with_salary} ({with_salary/len(self.jobs)*100:.1f}%)")
        
        # Contract types
        contract_types = {}
        for job in self.jobs:
            ct = job.get('contract_type', 'Unknown')
            contract_types[ct] = contract_types.get(ct, 0) + 1
        
        print(f"\nContract Types:")
        for ct, count in sorted(contract_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ct}: {count}")
        
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Reed.co.uk Job Scraper')
    parser.add_argument('--keywords', '-k', required=True, help='Job keywords to search')
    parser.add_argument('--location', '-l', default='London', help='Location (default: London)')
    parser.add_argument('--max-results', '-m', type=int, default=50, help='Max results (default: 50)')
    parser.add_argument('--distance', '-d', type=int, default=10, help='Distance in miles (default: 10)')
    parser.add_argument('--salary-min', '-s', type=int, help='Minimum salary')
    parser.add_argument('--contract-type', '-c', choices=['permanent', 'contract', 'temp', 'parttime'], 
                       help='Contract type')
    parser.add_argument('--api-key', '-a', help='Reed API key')
    parser.add_argument('--use-api', action='store_true', help='Use API instead of web scraping')
    parser.add_argument('--enrich', '-e', type=int, default=0, help='Enrich top N jobs with full details')
    parser.add_argument('--output', '-o', default='reed_jobs.json', help='Output file')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = ReedScraper(api_key=args.api_key)
    
    # Search jobs
    if args.use_api:
        if not args.api_key:
            logger.error("--api-key required for API search")
            return
        scraper.jobs = scraper.search_with_api(
            keywords=args.keywords,
            location=args.location,
            max_results=args.max_results,
            distance=args.distance,
            salary_min=args.salary_min
        )
    else:
        scraper.search_jobs(
            job_title=args.keywords,
            location=args.location,
            max_results=args.max_results,
            distance=args.distance,
            salary_min=args.salary_min,
            contract_type=args.contract_type
        )
    
    # Enrich with details
    if args.enrich > 0:
        scraper.enrich_jobs_with_details(args.enrich)
    
    # Save and print summary
    scraper.save_jobs(args.output)
    scraper.print_summary()


if __name__ == "__main__":
    main()
