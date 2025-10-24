#!/usr/bin/env python3
"""
Enhanced Reed.co.uk Job Scraper
Professional web scraping with API support, advanced filtering, and robust error handling
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin, urlencode
import logging
from typing import List, Dict, Optional, Set, Tuple
import re
import argparse
from dataclasses import dataclass, asdict
from functools import wraps
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reed_scraper.log'),
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
    contract_type: str
    description_snippet: str
    url: str
    posted_date: str
    source: str
    scraped_at: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    full_description: Optional[str] = None
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    employment_type: Optional[str] = None
    expiration_date: Optional[str] = None
    remote_option: bool = False


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    """Decorator for retrying failed operations with exponential backoff"""
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
    """Advanced rate limiter with burst allowance"""
    def __init__(self, requests_per_minute: int = 30, burst: int = 5):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.min_interval = 60.0 / requests_per_minute
        self.request_times: List[float] = []
    
    def wait(self):
        """Wait if necessary to respect rate limits"""
        now = time.time()
        
        # Remove old requests outside the time window
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Check if we're within burst limit
        if len(self.request_times) < self.burst:
            self.request_times.append(now)
            return
        
        # Check if we're within rate limit
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
                now = time.time()
        
        # Ensure minimum interval between requests
        if self.request_times:
            elapsed = now - self.request_times[-1]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        
        self.request_times.append(time.time())


class ReedScraper:
    """Enhanced Reed.co.uk job scraper with API and web scraping capabilities"""
    
    BASE_URL = "https://www.reed.co.uk"
    API_URL = "https://www.reed.co.uk/api/1.0/search"
    
    def __init__(self, api_key: Optional[str] = None, requests_per_minute: int = 30):
        self.api_key = api_key
        self.session = self._create_session()
        self.jobs: List[JobListing] = []
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.seen_job_ids: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
    def _create_session(self) -> requests.Session:
        """Create configured requests session with realistic headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        })
        return session
    
    @retry_on_failure(max_retries=3)
    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with retry logic and rate limiting"""
        self.rate_limiter.wait()
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return response
    
    def search_jobs(self, 
                   job_title: str, 
                   location: str = "London", 
                   max_results: int = 100,
                   distance: int = 10,
                   salary_min: Optional[int] = None,
                   salary_max: Optional[int] = None,
                   contract_type: Optional[str] = None,
                   posted_days: Optional[int] = None,
                   remote_only: bool = False) -> List[JobListing]:
        """
        Web scraping method for Reed jobs with advanced filtering
        
        Args:
            job_title: Job title or keywords
            location: Location to search
            max_results: Maximum number of results
            distance: Search radius in miles
            salary_min: Minimum salary (annual)
            salary_max: Maximum salary (annual)
            contract_type: permanent, contract, temp, parttime
            posted_days: Jobs posted within X days (1, 3, 7, 14, 30)
            remote_only: Filter for remote jobs only
        
        Returns:
            List of JobListing objects
        """
        logger.info(f"🔍 Scraping Reed for: '{job_title}' in '{location}'")
        logger.info(f"Filters: type={contract_type}, salary_min={salary_min}, distance={distance}mi")
        
        page = 1
        consecutive_failures = 0
        max_failures = 3
        
        while len(self.jobs) < max_results and consecutive_failures < max_failures:
            try:
                url = self._build_search_url(
                    job_title, location, page, distance, 
                    salary_min, salary_max, contract_type, posted_days, remote_only
                )
                
                logger.info(f"Fetching page {page}...")
                response = self._make_request(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards using multiple selectors
                job_cards = self._find_job_cards(soup)
                
                if not job_cards:
                    consecutive_failures += 1
                    logger.warning(f"No jobs found on page {page}")
                    if consecutive_failures >= max_failures:
                        logger.info("Multiple empty pages, ending search")
                        break
                    page += 1
                    time.sleep(random.uniform(2, 4))
                    continue
                
                consecutive_failures = 0
                jobs_added = 0
                
                for card in job_cards:
                    if len(self.jobs) >= max_results:
                        break
                    
                    job_data = self._parse_job_card(card)
                    if job_data and job_data.id not in self.seen_job_ids:
                        self.jobs.append(job_data)
                        self.seen_job_ids.add(job_data.id)
                        jobs_added += 1
                
                logger.info(f"Page {page}: Found {len(job_cards)} cards, Added {jobs_added} new jobs | Total: {len(self.jobs)}")
                
                # Check for next page
                if not self._has_next_page(soup):
                    logger.info("No more pages available")
                    break
                
                page += 1
                time.sleep(random.uniform(2, 5))
                
            except requests.RequestException as e:
                logger.error(f"Request failed on page {page}: {str(e)}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    break
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error on page {page}: {str(e)}", exc_info=True)
                consecutive_failures += 1
        
        logger.info(f"✅ Scraping complete: {len(self.jobs)} unique jobs found")
        return self.jobs
    
    def _build_search_url(self, job_title: str, location: str, page: int,
                         distance: int, salary_min: Optional[int], salary_max: Optional[int],
                         contract_type: Optional[str], posted_days: Optional[int],
                         remote_only: bool) -> str:
        """Build Reed search URL with all parameters"""
        keywords = quote_plus(job_title)
        loc = quote_plus(location)
        
        # Base URL structure
        url = f"{self.BASE_URL}/jobs/{keywords}-jobs"
        
        # Add location if not searching everywhere
        if location.lower() not in ['uk', 'united kingdom', 'anywhere']:
            url += f"-in-{loc}"
        
        # Build query parameters
        params = {
            'pageno': page,
            'sortby': 'date'  # Sort by most recent
        }
        
        if distance:
            params['proximity'] = distance
        
        if salary_min:
            params['salaryfrom'] = salary_min
        
        if salary_max:
            params['salaryto'] = salary_max
        
        if contract_type:
            params['contracttype'] = contract_type
        
        if posted_days:
            params['datecreatedoffset'] = posted_days
        
        if remote_only:
            params['locationtype'] = 'remote'
        
        # Construct final URL
        if params:
            url += '?' + urlencode(params)
        
        return url
    
    def _find_job_cards(self, soup: BeautifulSoup) -> List:
        """Find job cards using multiple selectors"""
        selectors = [
            ('article', {'class': 'job-result'}),
            ('article', {'class': re.compile(r'job-card')}),
            ('div', {'data-qa': 'job-card'}),
            ('div', {'class': 'job-result-card'}),
            ('article', None)  # Fallback to all articles
        ]
        
        for tag, attrs in selectors:
            if attrs:
                cards = soup.find_all(tag, attrs)
            else:
                # Fallback: find all articles and filter by content
                cards = soup.find_all(tag)
                cards = [c for c in cards if c.find('h2') or c.find('a', href=re.compile(r'/jobs/'))]
            
            if cards:
                logger.debug(f"Found {len(cards)} job cards using selector: {tag} {attrs}")
                return cards
        
        return []
    
    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page"""
        # Multiple ways to detect next page
        next_indicators = [
            soup.find('a', {'aria-label': 'Next page'}),
            soup.find('a', {'rel': 'next'}),
            soup.find('a', string=re.compile(r'Next', re.I)),
            soup.find('li', {'class': 'pagination-next'})
        ]
        
        return any(indicator is not None for indicator in next_indicators)
    
    def _parse_job_card(self, card) -> Optional[JobListing]:
        """Parse individual Reed job card with comprehensive extraction"""
        try:
            # Job title and URL
            title_elem = self._find_element(card, [
                ('h2', {'class': 'job-result-heading__title'}),
                ('h2', {'class': re.compile(r'job.*title')}),
                ('a', {'data-qa': 'job-card-title'}),
                ('h2', None)
            ])
            
            if not title_elem:
                return None
            
            title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
            job_title = self._clean_text(title_link.get_text() if title_link else title_elem.get_text())
            
            if not job_title:
                return None
            
            job_url = ""
            if title_link and title_link.get('href'):
                job_url = urljoin(self.BASE_URL, title_link['href'])
            
            # Extract job ID from URL
            job_id = self._extract_job_id(job_url)
            if not job_id:
                # Generate hash-based ID if extraction fails
                job_id = hashlib.md5(f"{job_title}{job_url}".encode()).hexdigest()[:16]
            
            # Company name
            company_elem = self._find_element(card, [
                ('a', {'class': 'gtmJobListingPostedBy'}),
                ('a', {'data-qa': 'job-card-company'}),
                ('span', {'class': re.compile(r'company')}),
                ('div', {'class': 'posted-by'})
            ])
            company = self._clean_text(company_elem.get_text() if company_elem else "Unknown")
            
            # Location
            location_elem = self._find_element(card, [
                ('li', {'class': 'job-metadata__item--location'}),
                ('span', {'data-qa': 'job-card-location'}),
                ('div', {'class': 'location'}),
                ('span', {'class': re.compile(r'location')})
            ])
            location = self._clean_text(location_elem.get_text() if location_elem else "")
            location = location.replace('Location', '').replace('location', '').strip()
            
            # Check for remote
            remote_option = 'remote' in location.lower() or 'home' in location.lower()
            
            # Salary
            salary_elem = self._find_element(card, [
                ('li', {'class': 'job-metadata__item--salary'}),
                ('span', {'data-qa': 'job-card-salary'}),
                ('div', {'class': 'salary'}),
                ('span', {'class': re.compile(r'salary')})
            ])
            salary_text = self._clean_text(salary_elem.get_text() if salary_elem else "")
            salary_text = salary_text.replace('Salary', '').replace('salary', '').strip()
            
            # Parse salary range
            salary_min, salary_max = self._parse_salary(salary_text)
            
            # Contract type
            contract_elem = self._find_element(card, [
                ('li', {'class': 'job-metadata__item--type'}),
                ('span', {'data-qa': 'job-card-type'}),
                ('div', {'class': 'contract-type'}),
                ('span', {'class': re.compile(r'contract')})
            ])
            contract_type = self._clean_text(contract_elem.get_text() if contract_elem else "")
            
            # Job description snippet
            desc_elem = self._find_element(card, [
                ('p', {'class': 'job-result-description__details'}),
                ('div', {'data-qa': 'job-card-description'}),
                ('div', {'class': 'job-result-description'}),
                ('p', {'class': re.compile(r'description')})
            ])
            description = self._clean_text(desc_elem.get_text() if desc_elem else "")
            
            # Posted date
            date_elem = self._find_element(card, [
                ('li', {'class': 'job-metadata__item--date'}),
                ('span', {'data-qa': 'job-card-date'}),
                ('time', None),
                ('span', {'class': re.compile(r'date')})
            ])
            posted_date = self._clean_text(date_elem.get_text() if date_elem else "")
            posted_date = posted_date.replace('Posted', '').replace('posted', '').strip()
            
            return JobListing(
                id=job_id,
                title=job_title,
                company=company,
                location=location,
                salary=salary_text,
                salary_min=salary_min,
                salary_max=salary_max,
                contract_type=contract_type,
                description_snippet=description,
                url=job_url,
                posted_date=posted_date,
                remote_option=remote_option,
                source='reed',
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.debug(f"Error parsing job card: {str(e)}")
            return None
    
    def _find_element(self, parent, selectors: List[Tuple]) -> Optional:
        """Try multiple selectors to find an element"""
        for tag, attrs in selectors:
            if attrs:
                elem = parent.find(tag, attrs)
            else:
                elem = parent.find(tag)
            if elem:
                return elem
        return None
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from Reed URL"""
        if not url:
            return ""
        
        # Pattern: /jobs/job-title/12345678
        match = re.search(r'/(\d{7,10})(?:\?|$)', url)
        if match:
            return match.group(1)
        
        # Alternative pattern
        match = re.search(r'jobId[=/](\d+)', url, re.I)
        if match:
            return match.group(1)
        
        return ""
    
    def _parse_salary(self, salary_text: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse salary text into min and max values"""
        if not salary_text:
            return None, None
        
        # Remove currency symbols and normalize
        cleaned = re.sub(r'[£$,]', '', salary_text)
        
        # Handle ranges: "30000 - 40000" or "30k - 40k"
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:k|K)?\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*(?:k|K)?', cleaned)
        if range_match:
            min_sal = float(range_match.group(1))
            max_sal = float(range_match.group(2))
            
            # Convert k notation
            if 'k' in salary_text.lower():
                min_sal *= 1000
                max_sal *= 1000
            
            # Convert hourly to annual
            if 'hour' in salary_text.lower() or 'hr' in salary_text.lower():
                min_sal *= 2080
                max_sal *= 2080
            elif 'day' in salary_text.lower():
                min_sal *= 260  # ~52 weeks * 5 days
                max_sal *= 260
            
            return min_sal, max_sal
        
        # Single value: "40000" or "40k"
        single_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:k|K)?', cleaned)
        if single_match:
            salary = float(single_match.group(1))
            
            if 'k' in salary_text.lower():
                salary *= 1000
            
            if 'hour' in salary_text.lower() or 'hr' in salary_text.lower():
                salary *= 2080
            elif 'day' in salary_text.lower():
                salary *= 260
            
            # For single values, set both min and max
            return salary, salary
        
        return None, None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    @retry_on_failure(max_retries=2)
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Fetch full job details from job page"""
        if not job_url or job_url in self.failed_urls:
            return None
        
        try:
            logger.debug(f"Fetching job details: {job_url}")
            response = self._make_request(job_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Full job description
            desc_elem = soup.find('div', itemprop='description')
            if not desc_elem:
                desc_elem = soup.find('span', itemprop='description')
            if not desc_elem:
                desc_elem = soup.find('div', {'class': re.compile(r'job.*description')})
            
            if desc_elem:
                details['full_description'] = self._clean_text(desc_elem.get_text('\n'))
                
                # Extract structured information
                requirements = self._extract_requirements(desc_elem)
                if requirements:
                    details['requirements'] = requirements
            
            # Benefits
            benefits = []
            benefits_section = soup.find('div', {'class': re.compile(r'benefits')})
            if benefits_section:
                benefit_items = benefits_section.find_all(['li', 'p'])
                benefits = [self._clean_text(item.get_text()) for item in benefit_items if item.get_text().strip()]
                if benefits:
                    details['benefits'] = benefits
            
            # Additional salary info
            salary_detail = soup.find('span', itemprop='baseSalary')
            if salary_detail:
                details['salary_detail'] = self._clean_text(salary_detail.get_text())
            
            # Employment type
            emp_type = soup.find('span', itemprop='employmentType')
            if emp_type:
                details['employment_type'] = self._clean_text(emp_type.get_text())
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching job details from {job_url}: {str(e)}")
            self.failed_urls.add(job_url)
            return None
    
    def _extract_requirements(self, description_elem) -> List[str]:
        """Extract requirements from job description"""
        requirements = []
        text = description_elem.get_text()
        
        # Look for requirements sections
        patterns = [
            r'(?:Requirements?|Qualifications?|Essential Skills?|Must Have):(.+?)(?:Responsibilities|Benefits|About|Nice to Have|Desirable|$)',
            r'(?:You will have|You must have|You should have):(.+?)(?:Responsibilities|Benefits|About|$)',
            r'(?:Essential|Required):(.+?)(?:Desirable|Nice to Have|Benefits|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                req_text = match.group(1)
                
                # Try to extract bullet points
                bullets = re.findall(r'[•\-\*]\s*(.+?)(?=\n|$)', req_text)
                if bullets:
                    requirements.extend([self._clean_text(b) for b in bullets[:15]])
                else:
                    # Extract lines
                    lines = [self._clean_text(line) for line in req_text.split('\n') if len(line.strip()) > 10]
                    requirements.extend(lines[:10])
                
                if requirements:
                    break
        
        return requirements[:15]  # Limit to 15 items
    
    def search_with_api(self, 
                       keywords: str,
                       location: str = "London",
                       max_results: int = 100,
                       distance: int = 10,
                       salary_min: Optional[int] = None,
                       salary_max: Optional[int] = None,
                       contract_type: Optional[str] = None) -> List[JobListing]:
        """
        Search using Reed API (requires API key)
        Get your API key from: https://www.reed.co.uk/developers/jobseeker
        """
        if not self.api_key:
            logger.error("❌ API key required. Get one from: https://www.reed.co.uk/developers/jobseeker")
            return []
        
        logger.info(f"🔍 Searching Reed API for: '{keywords}' in '{location}'")
        
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
            if salary_max:
                params['maximumSalary'] = salary_max
            if contract_type:
                params['contractType'] = contract_type
            
            try:
                self.rate_limiter.wait()
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
                    job_id = str(job.get('jobId', ''))
                    
                    if job_id in self.seen_job_ids:
                        continue
                    
                    min_sal = job.get('minimumSalary')
                    max_sal = job.get('maximumSalary')
                    
                    job_data = JobListing(
                        id=job_id,
                        title=job.get('jobTitle', ''),
                        company=job.get('employerName', ''),
                        location=job.get('locationName', ''),
                        salary=self._format_salary_display(min_sal, max_sal),
                        salary_min=float(min_sal) if min_sal else None,
                        salary_max=float(max_sal) if max_sal else None,
                        description_snippet=job.get('jobDescription', ''),
                        full_description=job.get('jobDescription', ''),
                        url=job.get('jobUrl', ''),
                        posted_date=job.get('date', ''),
                        contract_type=job.get('contractType', ''),
                        expiration_date=job.get('expirationDate', ''),
                        remote_option='remote' in job.get('locationName', '').lower(),
                        source='reed_api',
                        scraped_at=datetime.now().isoformat()
                    )
                    
                    all_results.append(job_data)
                    self.seen_job_ids.add(job_id)
                
                logger.info(f"Fetched {len(results)} jobs via API | Total: {len(all_results)}")
                time.sleep(0.5)
                
            except requests.RequestException as e:
                logger.error(f"API request failed: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Error processing API response: {str(e)}", exc_info=True)
                break
        
        logger.info(f"✅ Total jobs from API: {len(all_results)}")
        self.jobs = all_results
        return all_results
    
    def _format_salary_display(self, min_sal, max_sal) -> str:
        """Format salary range for display"""
        if not min_sal and not max_sal:
            return ""
        if min_sal and max_sal:
            return f"£{int(min_sal):,} - £{int(max_sal):,}"
        if min_sal:
            return f"£{int(min_sal):,}+"
        return f"Up to £{int(max_sal):,}"
    
    def enrich_jobs_with_details(self, max_jobs: int = 20):
        """Fetch full details for top jobs"""
        logger.info(f"📝 Enriching top {min(max_jobs, len(self.jobs))} jobs with full details...")
        
        enriched = 0
        for i, job in enumerate(self.jobs[:max_jobs]):
            if not job.url:
                continue
            
            logger.info(f"[{i+1}/{min(max_jobs, len(self.jobs))}] {job.title} at {job.company}")
            details = self.get_job_details(job.url)
            
            if details:
                job.full_description = details.get('full_description', job.full_description)
                job.requirements = details.get('requirements', job.requirements)
                job.benefits = details.get('benefits', job.benefits)
                job.employment_type = details.get('employment_type', job.employment_type)
                enriched += 1
            
            time.sleep(random.uniform(1.5, 3))
        
        logger.info(f"✅ Enriched {enriched} jobs with full details")
    
    def save_jobs(self, filename: str = 'reed_jobs.json', format: str = 'json'):
        """Save scraped jobs to file"""
        output_path = Path(filename)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                jobs_dict = [asdict(job) for job in self.jobs]
                json.dump(jobs_dict, f, indent=2, ensure_ascii=False)
        elif format == 'csv':
            import csv
            csv_path = output_path.with_suffix('.csv')
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                if self.jobs:
                    fieldnames = asdict(self.jobs[0]).keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for job in self.jobs:
                        row = asdict(job)
                        # Convert lists to strings for CSV
                        for key, value in row.items():
                            if isinstance(value, list):
                                row[key] = '; '.join(str(v) for v in value)
                        writer.writerow(row)
            logger.info(f"💾 Saved {len(self.jobs)} jobs to {csv_path}")
            return
        
        logger.info(f"💾 Saved {len(self.jobs)} jobs to {output_path}")
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about scraped jobs"""
        if not self.jobs:
            return {}
        
        stats = {
            'total_jobs': len(self.jobs),
            'unique_companies': len(set(j.company for j in self.jobs if j.company != 'Unknown')),
            'unique_locations': len(set(j.location for j in self.jobs if j.location)),
            'with_salary': sum(1 for j in self.jobs if j.salary),
            'remote_jobs': sum(1 for j in self.jobs if j.remote_option),
            'with_full_description': sum(1 for j in self.jobs if j.full_description),
            'contract_types': {},
            'top_companies': {},
            'top_locations': {}
        }
        
        # Contract type distribution
        for job in self.jobs:
            ct = job.contract_type or 'Unknown'
            stats['contract_types'][ct] = stats['contract_types'].get(ct, 0) + 1
        
        # Top companies
        for job in self.jobs:
            if job.company != 'Unknown':
                stats['top_companies'][job.company] = stats['top_companies'].get(job.company, 0) + 1
        
        # Top locations
        for job in self.jobs:
            if job.location:
                stats['top_locations'][job.location] = stats['top_locations'].get(job.location, 0) + 1
        
        # Salary statistics
        salaries = [j.salary_min for j in self.jobs if j.salary_min and j.salary_min > 0]
        if salaries:
            stats['avg_salary'] = sum(salaries) / len(salaries)
            stats['median_salary'] = sorted(salaries)[len(salaries) // 2]
            stats['min_salary'] = min(salaries)
            stats['max_salary'] = max(salaries)
        
        return stats
    
    def print_summary(self):
        """Print comprehensive scraping summary"""
        stats = self.get_statistics()
        
        if not stats:
            print("\n⚠️  No jobs to summarize")
            return
        
        print("\n" + "="*70)
        print("📊 REED SCRAPING SUMMARY")
        print("="*70)
        print(f"Total Jobs:           {stats['total_jobs']}")
        print(f"Unique Companies:     {stats['unique_companies']}")
        print(f"Unique Locations:     {stats['unique_locations']}")
        print(f"With Salary Info:     {stats['with_salary']} ({stats['with_salary']/stats['total_jobs']*100:.1f}%)")
        print(f"Remote Jobs:          {stats['remote_jobs']} ({stats['remote_jobs']/stats['total_jobs']*100:.1f}%)")
        print(f"Enriched (Full Desc): {stats['with_full_description']} ({stats['with_full_description']/stats['total_jobs']*100:.1f}%)")
        
        if 'avg_salary' in stats:
            print(f"\n💰 Salary Statistics:")
            print(f"  Average:  £{stats['avg_salary']:,.0f}")
            print(f"  Median:   £{stats['median_salary']:,.0f}")
            print(f"  Range:    £{stats['min_salary']:,.0f} - £{stats['max_salary']:,.0f}")
        
        print(f"\n📋 Contract Types:")
        for ct, count in sorted(stats['contract_types'].items(), key=lambda x: x[1], reverse=True):
            pct = (count / stats['total_jobs']) * 100
            print(f"  {ct:20} {count:3d} ({pct:5.1f}%)")
        
        if stats['top_companies']:
            print(f"\n🏢 Top 10 Companies:")
            for company, count in sorted(stats['top_companies'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {company[:40]:40} {count:3d}")
        
        if stats['top_locations']:
            print(f"\n📍 Top 10 Locations:")
            for location, count in sorted(stats['top_locations'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {location[:40]:40} {count:3d}")
        
        print("="*70 + "\n")
    
    def export_summary_report(self, filename: str = 'reed_summary.txt'):
        """Export detailed summary report"""
        stats = self.get_statistics()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("REED JOB SCRAPING SUMMARY REPORT\n")
            f.write("="*70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("OVERVIEW\n")
            f.write("-"*70 + "\n")
            f.write(f"Total Jobs Scraped:     {stats['total_jobs']}\n")
            f.write(f"Unique Companies:       {stats['unique_companies']}\n")
            f.write(f"Unique Locations:       {stats['unique_locations']}\n")
            f.write(f"Jobs with Salary Info:  {stats['with_salary']}\n")
            f.write(f"Remote Jobs:            {stats['remote_jobs']}\n\n")
            
            if 'avg_salary' in stats:
                f.write("SALARY ANALYSIS\n")
                f.write("-"*70 + "\n")
                f.write(f"Average Salary:  £{stats['avg_salary']:,.0f}\n")
                f.write(f"Median Salary:   £{stats['median_salary']:,.0f}\n")
                f.write(f"Salary Range:    £{stats['min_salary']:,.0f} - £{stats['max_salary']:,.0f}\n\n")
            
            f.write("CONTRACT TYPE DISTRIBUTION\n")
            f.write("-"*70 + "\n")
            for ct, count in sorted(stats['contract_types'].items(), key=lambda x: x[1], reverse=True):
                pct = (count / stats['total_jobs']) * 100
                f.write(f"{ct:25} {count:4d} ({pct:5.1f}%)\n")
        
        logger.info(f"📄 Summary report saved to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Reed.co.uk Job Scraper with API Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Web scraping
  %(prog)s -k "Python Developer" -l London -m 100
  %(prog)s -k "Data Analyst" -l Manchester --salary-min 35000 --contract permanent
  %(prog)s -k "DevOps Engineer" -l "United Kingdom" --remote --enrich 15
  
  # API usage (requires API key from https://www.reed.co.uk/developers/jobseeker)
  %(prog)s -k "Software Engineer" -l London --use-api --api-key YOUR_KEY
  %(prog)s -k "Java Developer" --use-api -a YOUR_KEY --salary-min 50000 -m 200
        """
    )
    
    # Search parameters
    parser.add_argument('--keywords', '-k', required=True, help='Job keywords/title to search')
    parser.add_argument('--location', '-l', default='London', help='Location (default: London)')
    parser.add_argument('--max-results', '--max', '-m', type=int, default=50, 
                       help='Maximum number of results (default: 50)')
    parser.add_argument('--distance', '-d', type=int, default=10, 
                       help='Search radius in miles (default: 10)')
    
    # Filters
    parser.add_argument('--salary-min', '-s', type=int, help='Minimum annual salary')
    parser.add_argument('--salary-max', type=int, help='Maximum annual salary')
    parser.add_argument('--contract-type', '-c', 
                       choices=['permanent', 'contract', 'temp', 'parttime'], 
                       help='Contract type filter')
    parser.add_argument('--posted-days', '-p', type=int, choices=[1, 3, 7, 14, 30],
                       help='Jobs posted within last N days')
    parser.add_argument('--remote', '-r', action='store_true', 
                       help='Filter for remote jobs only')
    
    # API options
    parser.add_argument('--api-key', '-a', help='Reed API key (get from https://www.reed.co.uk/developers/jobseeker)')
    parser.add_argument('--use-api', action='store_true', 
                       help='Use Reed API instead of web scraping')
    
    # Output options
    parser.add_argument('--enrich', '-e', type=int, default=0, 
                       help='Enrich top N jobs with full details (default: 0)')
    parser.add_argument('--output', '-o', default='reed_jobs.json', 
                       help='Output filename (default: reed_jobs.json)')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--summary-report', action='store_true',
                       help='Generate detailed summary report file')
    
    # Performance options
    parser.add_argument('--rate-limit', type=int, default=30,
                       help='Requests per minute (default: 30)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize scraper
    scraper = ReedScraper(api_key=args.api_key, requests_per_minute=args.rate_limit)
    
    # Search jobs
    if args.use_api:
        if not args.api_key:
            logger.error("❌ --api-key required for API search")
            logger.info("Get your API key from: https://www.reed.co.uk/developers/jobseeker")
            return 1
        
        jobs = scraper.search_with_api(
            keywords=args.keywords,
            location=args.location,
            max_results=args.max_results,
            distance=args.distance,
            salary_min=args.salary_min,
            salary_max=args.salary_max,
            contract_type=args.contract_type
        )
    else:
        jobs = scraper.search_jobs(
            job_title=args.keywords,
            location=args.location,
            max_results=args.max_results,
            distance=args.distance,
            salary_min=args.salary_min,
            salary_max=args.salary_max,
            contract_type=args.contract_type,
            posted_days=args.posted_days,
            remote_only=args.remote
        )
    
    if not jobs:
        logger.warning("❌ No jobs found. Try adjusting your search parameters.")
        return 1
    
    # Enrich with full details
    if args.enrich > 0:
        scraper.enrich_jobs_with_details(args.enrich)
    
    # Save results
    scraper.save_jobs(args.output, args.format)
    
    # Print summary
    scraper.print_summary()
    
    # Generate summary report
    if args.summary_report:
        scraper.export_summary_report('reed_summary.txt')
    
    print(f"✅ Scraping complete! {len(jobs)} jobs saved to {args.output}")
    return 0


if __name__ == "__main__":
    exit(main())
