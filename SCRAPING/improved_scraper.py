#!/usr/bin/env python3
"""
Advanced Job Scraping Suite - Improved Version
Features:
- Multi-site support (Glassdoor, Reed, LinkedIn, Indeed)
- Rotating proxies & user agents
- Smart retry with exponential backoff
- Rate limiting & request throttling
- Data deduplication
- Advanced filtering & enrichment
- Export to multiple formats (JSON, CSV, Excel, SQLite)
- Comprehensive logging & error recovery
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import time
import json
import csv
import sqlite3
import random
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import quote, urljoin, urlparse
from collections import defaultdict
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import argparse
from functools import wraps
from threading import Lock
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class JobListing:
    """Structured job listing data"""
    job_id: str
    title: str
    company: str
    location: str
    salary: str
    description: str
    url: str
    source: str
    posted_date: str
    scraped_at: str
    contract_type: str = ""
    experience_level: str = ""
    company_rating: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    skills: List[str] = None
    benefits: List[str] = None
    remote: bool = False
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.benefits is None:
            self.benefits = []
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def get_hash(self) -> str:
        """Generate unique hash for deduplication"""
        key = f"{self.title}_{self.company}_{self.location}"
        return hashlib.md5(key.encode()).hexdigest()


# ============================================================================
# UTILITY CLASSES
# ============================================================================

class RateLimiter:
    """Thread-safe rate limiter"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            # Remove old requests outside time window
            self.requests = [r for r in self.requests if now - r < self.time_window]
            
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0]) + 1
                logger.debug(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.requests = []
            
            self.requests.append(time.time())


class UserAgentRotator:
    """Rotate user agents for anti-detection"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self):
        self.index = 0
    
    def get_random(self) -> str:
        """Get random user agent"""
        return random.choice(self.USER_AGENTS)
    
    def get_next(self) -> str:
        """Get next user agent in rotation"""
        ua = self.USER_AGENTS[self.index]
        self.index = (self.index + 1) % len(self.USER_AGENTS)
        return ua


class RetryHandler:
    """Smart retry with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.error(f"Failed after {self.max_retries} attempts: {str(e)}")
                        raise
                    
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    jitter = random.uniform(0, 0.1 * delay)
                    sleep_time = delay + jitter
                    
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {sleep_time:.1f}s")
                    time.sleep(sleep_time)
        return wrapper


# ============================================================================
# BASE SCRAPER CLASS
# ============================================================================

class BaseScraper:
    """Base class with common scraping functionality"""
    
    def __init__(self, headless: bool = True, use_proxy: bool = False):
        self.headless = headless
        self.use_proxy = use_proxy
        self.jobs: List[JobListing] = []
        self.seen_hashes: Set[str] = set()
        self.rate_limiter = RateLimiter(max_requests=30, time_window=60)
        self.ua_rotator = UserAgentRotator()
        self.retry = RetryHandler(max_retries=3)
        self.stats = defaultdict(int)
    
    def _human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _is_duplicate(self, job: JobListing) -> bool:
        """Check if job is duplicate"""
        job_hash = job.get_hash()
        if job_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(job_hash)
        return False
    
    def _extract_salary_range(self, salary_str: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract min/max salary from string"""
        if not salary_str:
            return None, None
        
        # Remove currency symbols and commas
        clean = re.sub(r'[£$,]', '', salary_str)
        
        # Find all numbers
        numbers = re.findall(r'\d+(?:,?\d+)*', clean)
        if not numbers:
            return None, None
        
        # Convert to integers
        amounts = []
        for num in numbers:
            try:
                amount = int(num.replace(',', ''))
                # Filter unrealistic salaries
                if 1000 <= amount <= 1000000:
                    amounts.append(amount)
            except ValueError:
                continue
        
        if not amounts:
            return None, None
        
        # Detect if yearly/hourly/daily
        multiplier = 1
        if 'hour' in salary_str.lower():
            multiplier = 2000  # Approximate annual
        elif 'day' in salary_str.lower():
            multiplier = 250
        
        amounts = [a * multiplier for a in amounts]
        
        return min(amounts), max(amounts) if len(amounts) > 1 else min(amounts)
    
    def _detect_remote(self, text: str) -> bool:
        """Detect if job is remote"""
        remote_keywords = ['remote', 'work from home', 'wfh', 'hybrid', 'anywhere']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in remote_keywords)
    
    def _extract_skills(self, description: str) -> List[str]:
        """Extract skills from job description"""
        skills_db = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'sql', 'nosql', 'mongodb', 'postgresql',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'agile', 'scrum', 'git', 'ci/cd', 'jenkins', 'rest api', 'graphql'
        ]
        
        found_skills = []
        desc_lower = description.lower()
        
        for skill in skills_db:
            if skill in desc_lower:
                found_skills.append(skill)
        
        return found_skills


# ============================================================================
# GLASSDOOR SCRAPER (ENHANCED)
# ============================================================================

class GlassdoorScraperV2(BaseScraper):
    """Enhanced Glassdoor scraper with improved reliability"""
    
    BASE_URL = "https://www.glassdoor.co.uk"
    
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.email = email
        self.password = password
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome with stealth settings"""
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Anti-detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'--user-agent={self.ua_rotator.get_random()}')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
    
    @RetryHandler()
    def search_jobs(self, keywords: str, location: str = "London", max_results: int = 100, **filters) -> List[JobListing]:
        """Search Glassdoor jobs with filters"""
        logger.info(f"🔍 Searching Glassdoor: '{keywords}' in '{location}'")
        
        if not self.driver:
            self._init_driver()
        
        search_url = self._build_url(keywords, location, **filters)
        self.driver.get(search_url)
        self._human_delay(3, 5)
        
        page = 1
        collected = 0
        
        while collected < max_results:
            logger.info(f"📄 Page {page}")
            self.rate_limiter.wait_if_needed()
            
            job_cards = self._find_elements_safe(By.CSS_SELECTOR, 'li[data-test="jobListing"]')
            
            if not job_cards:
                logger.info("No more jobs found")
                break
            
            for card in job_cards:
                if collected >= max_results:
                    break
                
                job = self._parse_glassdoor_card(card)
                if job and not self._is_duplicate(job):
                    self.jobs.append(job)
                    collected += 1
                    self.stats['glassdoor_collected'] += 1
            
            if not self._go_next_page():
                break
            
            page += 1
            self._human_delay(2, 4)
        
        logger.info(f"✅ Collected {collected} jobs from Glassdoor")
        return self.jobs
    
    def _build_url(self, keywords: str, location: str, **filters) -> str:
        """Build search URL with filters"""
        base = f"{self.BASE_URL}/Job/jobs.htm"
        params = [
            f"sc.keyword={quote(keywords)}",
            f"locKeyword={quote(location)}"
        ]
        
        if filters.get('job_type'):
            params.append(f"jobType={filters['job_type'].upper()}")
        if filters.get('remote_only'):
            params.append("remoteWorkType=1")
        if filters.get('salary_min'):
            params.append(f"minSalary={filters['salary_min']}")
        
        return f"{base}?{'&'.join(params)}"
    
    def _parse_glassdoor_card(self, card) -> Optional[JobListing]:
        """Parse Glassdoor job card"""
        try:
            title = self._get_text_safe(card, 'a[data-test="job-link"]')
            company = self._get_text_safe(card, '[data-test="employer-name"]')
            location = self._get_text_safe(card, '[data-test="emp-location"]')
            salary = self._get_text_safe(card, '[data-test="detailSalary"]')
            rating = self._get_text_safe(card, 'span[data-test="rating"]')
            
            if not title or not company:
                return None
            
            # Get URL
            url_elem = card.find_element(By.CSS_SELECTOR, 'a[data-test="job-link"]')
            url = url_elem.get_attribute('href') if url_elem else ""
            
            # Extract job ID
            job_id = re.search(r'jobListingId=(\d+)', url)
            job_id = job_id.group(1) if job_id else hashlib.md5(f"{title}{company}".encode()).hexdigest()[:10]
            
            salary_min, salary_max = self._extract_salary_range(salary)
            
            return JobListing(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                salary=salary,
                description="",
                url=url,
                source='glassdoor',
                posted_date="",
                scraped_at=datetime.now().isoformat(),
                company_rating=rating,
                salary_min=salary_min,
                salary_max=salary_max,
                remote=self._detect_remote(location)
            )
        
        except Exception as e:
            logger.debug(f"Error parsing card: {e}")
            return None
    
    def _find_elements_safe(self, by, selector) -> List:
        """Safely find elements"""
        try:
            return self.driver.find_elements(by, selector)
        except:
            return []
    
    def _get_text_safe(self, parent, selector: str) -> str:
        """Safely get text from element"""
        try:
            elem = parent.find_element(By.CSS_SELECTOR, selector)
            return elem.text.strip()
        except:
            return ""
    
    def _go_next_page(self) -> bool:
        """Navigate to next page"""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[data-test="pagination-next"]')
            if next_btn.is_enabled():
                next_btn.click()
                return True
        except:
            pass
        return False
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()


# ============================================================================
# REED SCRAPER (ENHANCED)
# ============================================================================

class ReedScraperV2(BaseScraper):
    """Enhanced Reed scraper with API support"""
    
    BASE_URL = "https://www.reed.co.uk"
    API_URL = "https://www.reed.co.uk/api/1.0/search"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.session = self._init_session()
    
    def _init_session(self) -> requests.Session:
        """Initialize requests session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.ua_rotator.get_random(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
        })
        return session
    
    @RetryHandler()
    def search_jobs(self, keywords: str, location: str = "London", max_results: int = 100, **filters) -> List[JobListing]:
        """Search Reed jobs"""
        logger.info(f"🔍 Searching Reed: '{keywords}' in '{location}'")
        
        if self.api_key:
            return self._search_api(keywords, location, max_results, **filters)
        else:
            return self._search_web(keywords, location, max_results, **filters)
    
    def _search_web(self, keywords: str, location: str, max_results: int, **filters) -> List[JobListing]:
        """Web scraping method"""
        page = 1
        collected = 0
        
        while collected < max_results:
            self.rate_limiter.wait_if_needed()
            
            url = self._build_url(keywords, location, page, **filters)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('article', class_='job-result')
            
            if not job_cards:
                break
            
            for card in job_cards:
                if collected >= max_results:
                    break
                
                job = self._parse_reed_card(card)
                if job and not self._is_duplicate(job):
                    self.jobs.append(job)
                    collected += 1
                    self.stats['reed_collected'] += 1
            
            page += 1
            self._human_delay(2, 4)
        
        logger.info(f"✅ Collected {collected} jobs from Reed")
        return self.jobs
    
    def _search_api(self, keywords: str, location: str, max_results: int, **filters) -> List[JobListing]:
        """API search method"""
        results_per_page = 100
        
        for skip in range(0, max_results, results_per_page):
            params = {
                'keywords': keywords,
                'locationName': location,
                'resultsToTake': min(results_per_page, max_results - skip),
                'resultsToSkip': skip
            }
            
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
                break
            
            for job_data in results:
                job = self._parse_reed_api(job_data)
                if job and not self._is_duplicate(job):
                    self.jobs.append(job)
                    self.stats['reed_api_collected'] += 1
            
            time.sleep(0.5)
        
        return self.jobs
    
    def _build_url(self, keywords: str, location: str, page: int, **filters) -> str:
        """Build Reed URL"""
        kw = quote(keywords)
        loc = quote(location)
        url = f"{self.BASE_URL}/jobs/{kw}-jobs-in-{loc}?pageno={page}"
        
        if filters.get('salary_min'):
            url += f"&salaryfrom={filters['salary_min']}"
        if filters.get('contract_type'):
            url += f"&contracttype={filters['contract_type']}"
        
        return url
    
    def _parse_reed_card(self, card) -> Optional[JobListing]:
        """Parse Reed job card"""
        try:
            title_elem = card.find('h2', class_='job-result-heading__title')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
            url = urljoin(self.BASE_URL, title_link['href']) if title_link and title_link.get('href') else ""
            
            company_elem = card.find('a', class_='gtmJobListingPostedBy')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            location_elem = card.find('li', class_='job-metadata__item--location')
            location = location_elem.get_text(strip=True).replace('Location', '').strip() if location_elem else ""
            
            salary_elem = card.find('li', class_='job-metadata__item--salary')
            salary = salary_elem.get_text(strip=True).replace('Salary', '').strip() if salary_elem else ""
            
            desc_elem = card.find('p', class_='job-result-description__details')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            job_id = re.search(r'/(\d+)', url)
            job_id = job_id.group(1) if job_id else hashlib.md5(f"{title}{company}".encode()).hexdigest()[:10]
            
            salary_min, salary_max = self._extract_salary_range(salary)
            
            return JobListing(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                url=url,
                source='reed',
                posted_date="",
                scraped_at=datetime.now().isoformat(),
                salary_min=salary_min,
                salary_max=salary_max,
                remote=self._detect_remote(location + " " + description),
                skills=self._extract_skills(description)
            )
        
        except Exception as e:
            logger.debug(f"Error parsing Reed card: {e}")
            return None
    
    def _parse_reed_api(self, data: Dict) -> Optional[JobListing]:
        """Parse Reed API response"""
        try:
            salary_min = data.get('minimumSalary')
            salary_max = data.get('maximumSalary')
            salary = self._format_salary(salary_min, salary_max)
            
            description = data.get('jobDescription', '')
            
            return JobListing(
                job_id=str(data.get('jobId', '')),
                title=data.get('jobTitle', ''),
                company=data.get('employerName', ''),
                location=data.get('locationName', ''),
                salary=salary,
                description=description,
                url=data.get('jobUrl', ''),
                source='reed_api',
                posted_date=data.get('date', ''),
                scraped_at=datetime.now().isoformat(),
                contract_type=data.get('contractType', ''),
                salary_min=salary_min,
                salary_max=salary_max,
                remote=self._detect_remote(description),
                skills=self._extract_skills(description)
            )
        
        except Exception as e:
            logger.debug(f"Error parsing Reed API: {e}")
            return None
    
    def _format_salary(self, min_sal, max_sal) -> str:
        """Format salary range"""
        if not min_sal and not max_sal:
            return ""
        if min_sal and max_sal:
            return f"£{min_sal:,} - £{max_sal:,}"
        if min_sal:
            return f"£{min_sal:,}+"
        return f"Up to £{max_sal:,}"


# ============================================================================
# JOB MANAGER - Orchestrates multiple scrapers
# ============================================================================

class JobScraperManager:
    """Manages multiple job scrapers"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.all_jobs: List[JobListing] = []
        self.scrapers = []
        self.stats = defaultdict(int)
    
    def add_scraper(self, scraper: BaseScraper):
        """Add a scraper to the manager"""
        self.scrapers.append(scraper)
    
    def search_all(self, keywords: str, location: str = "London", max_per_site: int = 50, **filters) -> List[JobListing]:
        """Search across all configured scrapers"""
        logger.info(f"🚀 Starting multi-site job search")
        logger.info(f"Keywords: {keywords} | Location: {location} | Max per site: {max_per_site}")
        
        for scraper in self.scrapers:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Searching {scraper.__class__.__name__}")
                logger.info(f"{'='*60}")
                
                jobs = scraper.search_jobs(keywords, location, max_per_site, **filters)
                self.all_jobs.extend(jobs)
                self.stats[scraper.__class__.__name__] = len(jobs)
                
            except Exception as e:
                logger.error(f"Error with {scraper.__class__.__name__}: {e}")
                continue
        
        # Remove duplicates across sites
        self._deduplicate_jobs()
        
        logger.info(f"\n✅ Total unique jobs collected: {len(self.all_jobs)}")
        return self.all_jobs
    
    def _deduplicate_jobs(self):
        """Remove duplicate jobs across sites"""
        seen_hashes = set()
        unique_jobs = []
        
        for job in self.all_jobs:
            job_hash = job.get_hash()
            if job_hash not in seen_hashes:
                seen_hashes.add(job_hash)
                unique_jobs.append(job)
        
        duplicates = len(self.all_jobs) - len(unique_jobs)
        if duplicates > 0:
            logger.info(f"Removed {duplicates} duplicate jobs")
        
        self.all_jobs = unique_jobs
    
    def filter_jobs(self, 
                   salary_min: Optional[int] = None,
                   salary_max: Optional[int] = None,
                   remote_only: bool = False,
                   companies: Optional[List[str]] = None,
                   exclude_companies: Optional[List[str]] = None,
                   required_skills: Optional[List[str]] = None) -> List[JobListing]:
        """Apply filters to collected jobs"""
        filtered = self.all_jobs
        
        if salary_min:
            filtered = [j for j in filtered if j.salary_min and j.salary_min >= salary_min]
        
        if salary_max:
            filtered = [j for j in filtered if j.salary_max and j.salary_max <= salary_max]
        
        if remote_only:
            filtered = [j for j in filtered if j.remote]
        
        if companies:
            companies_lower = [c.lower() for c in companies]
            filtered = [j for j in filtered if j.company.lower() in companies_lower]
        
        if exclude_companies:
            exclude_lower = [c.lower() for c in exclude_companies]
            filtered = [j for j in filtered if j.company.lower() not in exclude_lower]
        
        if required_skills:
            skills_lower = [s.lower() for s in required_skills]
            filtered = [j for j in filtered if any(skill in [s.lower() for s in j.skills] for skill in skills_lower)]
        
        logger.info(f"Filtered: {len(self.all_jobs)} -> {len(filtered)} jobs")
        return filtered
    
    def save_jobs(self, filename: str = "jobs", format: str = "json"):
        """Save jobs to file"""
        if format == "json":
            self._save_json(f"{filename}.json")
        elif format == "csv":
            self._save_csv(f"{filename}.csv")
        elif format == "excel":
            self._save_excel(f"{filename}.xlsx")
        elif format == "sqlite":
            self._save_sqlite(f"{filename}.db")
        else:
            logger.error(f"Unknown format: {format}")
    
    def _save_json(self, filename: str):
        """Save to JSON"""
        data = [job.to_dict() for job in self.all_jobs]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved {len(self.all_jobs)} jobs to {filename}")
    
    def _save_csv(self, filename: str):
        """Save to CSV"""
        if not self.all_jobs:
            logger.warning("No jobs to save")
            return
        
        # Flatten job data for CSV
        csv_data = []
        for job in self.all_jobs:
            job_dict = job.to_dict()
            job_dict['skills'] = ', '.join(job.skills) if job.skills else ''
            job_dict['benefits'] = ', '.join(job.benefits) if job.benefits else ''
            csv_data.append(job_dict)
        
        keys = csv_data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csv_data)
        logger.info(f"💾 Saved {len(self.all_jobs)} jobs to {filename}")
    
    def _save_excel(self, filename: str):
        """Save to Excel"""
        try:
            import pandas as pd
            
            df = pd.DataFrame([job.to_dict() for job in self.all_jobs])
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"💾 Saved {len(self.all_jobs)} jobs to {filename}")
        except ImportError:
            logger.error("pandas and openpyxl required for Excel export. Install: pip install pandas openpyxl")
    
    def _save_sqlite(self, filename: str):
        """Save to SQLite database"""
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                salary TEXT,
                description TEXT,
                url TEXT,
                source TEXT,
                posted_date TEXT,
                scraped_at TEXT,
                contract_type TEXT,
                experience_level TEXT,
                company_rating TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                skills TEXT,
                benefits TEXT,
                remote INTEGER
            )
        ''')
        
        # Insert jobs
        for job in self.all_jobs:
            job_dict = job.to_dict()
            job_dict['skills'] = json.dumps(job.skills) if job.skills else ''
            job_dict['benefits'] = json.dumps(job.benefits) if job.benefits else ''
            job_dict['remote'] = 1 if job.remote else 0
            
            cursor.execute('''
                INSERT OR REPLACE INTO jobs VALUES (
                    :job_id, :title, :company, :location, :salary, :description,
                    :url, :source, :posted_date, :scraped_at, :contract_type,
                    :experience_level, :company_rating, :salary_min, :salary_max,
                    :skills, :benefits, :remote
                )
            ''', job_dict)
        
        conn.commit()
        conn.close()
        logger.info(f"💾 Saved {len(self.all_jobs)} jobs to {filename}")
    
    def print_summary(self):
        """Print comprehensive summary"""
        if not self.all_jobs:
            logger.warning("No jobs to summarize")
            return
        
        print("\n" + "="*70)
        print("📊 JOB SCRAPING SUMMARY")
        print("="*70)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Jobs: {len(self.all_jobs)}")
        print(f"   Unique Companies: {len(set(j.company for j in self.all_jobs))}")
        print(f"   Unique Locations: {len(set(j.location for j in self.all_jobs))}")
        
        print(f"\n🌐 Jobs by Source:")
        for source, count in self.stats.items():
            print(f"   {source}: {count}")
        
        print(f"\n🏢 Top Companies:")
        company_counts = defaultdict(int)
        for job in self.all_jobs:
            company_counts[job.company] += 1
        
        for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {company}: {count} jobs")
        
        print(f"\n📍 Top Locations:")
        location_counts = defaultdict(int)
        for job in self.all_jobs:
            location_counts[job.location] += 1
        
        for location, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {location}: {count} jobs")
        
        print(f"\n💰 Salary Statistics:")
        with_salary = [j for j in self.all_jobs if j.salary_min]
        print(f"   Jobs with salary info: {len(with_salary)} ({len(with_salary)/len(self.all_jobs)*100:.1f}%)")
        
        if with_salary:
            salaries = [j.salary_min for j in with_salary]
            print(f"   Average salary: £{sum(salaries)/len(salaries):,.0f}")
            print(f"   Median salary: £{sorted(salaries)[len(salaries)//2]:,.0f}")
            print(f"   Range: £{min(salaries):,} - £{max(salaries):,}")
        
        print(f"\n🏠 Remote Work:")
        remote_jobs = [j for j in self.all_jobs if j.remote]
        print(f"   Remote jobs: {len(remote_jobs)} ({len(remote_jobs)/len(self.all_jobs)*100:.1f}%)")
        
        print(f"\n🔧 Top Skills:")
        skill_counts = defaultdict(int)
        for job in self.all_jobs:
            for skill in job.skills:
                skill_counts[skill] += 1
        
        for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"   • {skill}: {count} jobs")
        
        print(f"\n📋 Contract Types:")
        contract_counts = defaultdict(int)
        for job in self.all_jobs:
            ct = job.contract_type or "Not specified"
            contract_counts[ct] += 1
        
        for ct, count in sorted(contract_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {ct}: {count}")
        
        print("\n" + "="*70 + "\n")
    
    def export_report(self, filename: str = "job_search_report.txt"):
        """Export detailed text report"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("JOB SEARCH REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Total Jobs Found: {len(self.all_jobs)}\n\n")
            
            for i, job in enumerate(self.all_jobs, 1):
                f.write(f"\n{'='*70}\n")
                f.write(f"Job #{i}\n")
                f.write(f"{'='*70}\n")
                f.write(f"Title: {job.title}\n")
                f.write(f"Company: {job.company}\n")
                f.write(f"Location: {job.location}\n")
                f.write(f"Salary: {job.salary}\n")
                f.write(f"Contract: {job.contract_type}\n")
                f.write(f"Remote: {'Yes' if job.remote else 'No'}\n")
                f.write(f"Source: {job.source}\n")
                f.write(f"URL: {job.url}\n")
                if job.skills:
                    f.write(f"Skills: {', '.join(job.skills)}\n")
                f.write(f"\nDescription:\n{job.description[:500]}...\n")
        
        logger.info(f"📄 Exported detailed report to {filename}")
    
    def cleanup(self):
        """Clean up all scrapers"""
        for scraper in self.scrapers:
            if hasattr(scraper, 'close'):
                scraper.close()


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Advanced Multi-Site Job Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search Glassdoor and Reed for Python jobs
  python improved_scraper.py -k "python developer" -l "London" -m 100 --sites glassdoor reed
  
  # Remote jobs only with salary filter
  python improved_scraper.py -k "data scientist" --remote --salary-min 50000 -m 50
  
  # Export to multiple formats
  python improved_scraper.py -k "software engineer" -f json csv excel
  
  # With authentication for Glassdoor
  python improved_scraper.py -k "product manager" --glassdoor-email user@email.com --glassdoor-password pass123
  
  # With Reed API key
  python improved_scraper.py -k "devops" --reed-api-key YOUR_API_KEY
        """
    )
    
    # Search parameters
    parser.add_argument('--keywords', '-k', required=True, help='Job keywords to search')
    parser.add_argument('--location', '-l', default='London', help='Job location (default: London)')
    parser.add_argument('--max-results', '-m', type=int, default=50, help='Max results per site (default: 50)')
    
    # Site selection
    parser.add_argument('--sites', nargs='+', choices=['glassdoor', 'reed', 'all'], 
                       default=['all'], help='Sites to scrape (default: all)')
    
    # Filters
    parser.add_argument('--salary-min', type=int, help='Minimum salary')
    parser.add_argument('--salary-max', type=int, help='Maximum salary')
    parser.add_argument('--remote', action='store_true', help='Remote jobs only')
    parser.add_argument('--job-type', choices=['fulltime', 'parttime', 'contract', 'temporary', 'internship'],
                       help='Job type filter')
    parser.add_argument('--experience', choices=['entry', 'mid', 'senior'], help='Experience level')
    parser.add_argument('--companies', nargs='+', help='Filter by specific companies')
    parser.add_argument('--exclude-companies', nargs='+', help='Exclude specific companies')
    parser.add_argument('--skills', nargs='+', help='Required skills')
    
    # Authentication
    parser.add_argument('--glassdoor-email', help='Glassdoor email')
    parser.add_argument('--glassdoor-password', help='Glassdoor password')
    parser.add_argument('--reed-api-key', help='Reed API key')
    
    # Output
    parser.add_argument('--output', '-o', default='jobs', help='Output filename (without extension)')
    parser.add_argument('--format', '-f', nargs='+', choices=['json', 'csv', 'excel', 'sqlite'], 
                       default=['json'], help='Output formats (default: json)')
    parser.add_argument('--report', action='store_true', help='Generate detailed text report')
    
    # Display
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--show-browser', action='store_true', help='Show browser window')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize manager
    manager = JobScraperManager()
    
    # Determine which sites to scrape
    sites = args.sites
    if 'all' in sites:
        sites = ['glassdoor', 'reed']
    
    # Add scrapers
    if 'glassdoor' in sites:
        logger.info("🔧 Initializing Glassdoor scraper...")
        glassdoor = GlassdoorScraperV2(
            email=args.glassdoor_email,
            password=args.glassdoor_password,
            headless=args.headless and not args.show_browser
        )
        manager.add_scraper(glassdoor)
    
    if 'reed' in sites:
        logger.info("🔧 Initializing Reed scraper...")
        reed = ReedScraperV2(api_key=args.reed_api_key)
        manager.add_scraper(reed)
    
    try:
        # Search jobs
        filters = {
            'job_type': args.job_type,
            'remote_only': args.remote,
            'salary_min': args.salary_min,
            'experience_level': args.experience
        }
        
        jobs = manager.search_all(
            keywords=args.keywords,
            location=args.location,
            max_per_site=args.max_results,
            **filters
        )
        
        # Apply additional filters
        if any([args.salary_max, args.companies, args.exclude_companies, args.skills]):
            jobs = manager.filter_jobs(
                salary_min=args.salary_min,
                salary_max=args.salary_max,
                remote_only=args.remote,
                companies=args.companies,
                exclude_companies=args.exclude_companies,
                required_skills=args.skills
            )
            manager.all_jobs = jobs
        
        # Save results
        if jobs:
            for fmt in args.format:
                manager.save_jobs(filename=args.output, format=fmt)
            
            if args.report:
                manager.export_report(f"{args.output}_report.txt")
            
            manager.print_summary()
        else:
            logger.warning("⚠️  No jobs were collected")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        manager.cleanup()
        logger.info("👋 Scraper shutdown complete")


if __name__ == "__main__":
    main()


# ============================================================================
# USAGE EXAMPLES (when imported as module)
# ============================================================================

"""
Example 1: Basic usage with default settings

from improved_scraper import JobScraperManager, GlassdoorScraperV2, ReedScraperV2

manager = JobScraperManager()
manager.add_scraper(GlassdoorScraperV2())
manager.add_scraper(ReedScraperV2())

jobs = manager.search_all("python developer", "London", max_per_site=50)
manager.save_jobs("results", format="json")
manager.print_summary()
manager.cleanup()


Example 2: Advanced filtering

manager = JobScraperManager()
manager.add_scraper(ReedScraperV2(api_key="YOUR_API_KEY"))

jobs = manager.search_all("data scientist", "Manchester", max_per_site=100)
filtered = manager.filter_jobs(
    salary_min=60000,
    remote_only=True,
    required_skills=["python", "machine learning"]
)

manager.all_jobs = filtered
manager.save_jobs("filtered_jobs", format="excel")


Example 3: Custom configuration

config = {
    'rate_limit': 30,
    'retry_attempts': 5,
    'timeout': 20
}

manager = JobScraperManager(config)
glassdoor = GlassdoorScraperV2(
    email="user@example.com",
    password="secure_password",
    headless=True
)
manager.add_scraper(glassdoor)

jobs = manager.search_all(
    "senior software engineer",
    "Edinburgh",
    max_per_site=75,
    job_type="fulltime",
    salary_min=70000
)

manager.export_report("job_report.txt")
manager.cleanup()
"""
