#!/usr/bin/env python3
"""
Enhanced Glassdoor Job Scraper
Advanced scraping with company reviews, ratings, and anti-detection
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import json
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
import argparse
import os
import re
from urllib.parse import quote, urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GlassdoorScraper:
    """Enhanced Glassdoor job scraper with company ratings and anti-detection"""
    
    BASE_URL = "https://www.glassdoor.co.uk"
    JOBS_URL = f"{BASE_URL}/Job/jobs.htm"
    
    # Common selectors (updated for 2025)
    SELECTORS = {
        'job_card': [
            'li[data-test="jobListing"]',
            'article.job-listing',
            'li.react-job-listing',
            'div[data-test="job-listing"]'
        ],
        'job_title': [
            'a[data-test="job-link"]',
            'a.JobCard_jobTitle__GLrfT',
            'a.job-title',
            'h2.jobTitle'
        ],
        'company_name': [
            '[data-test="employer-name"]',
            'span.EmployerProfile_employerName__Xemli',
            'span.employer-name',
            'div.company-name'
        ],
        'location': [
            '[data-test="emp-location"]',
            'div.JobCard_location__N_iYE',
            'span.location',
            'div.location'
        ],
        'salary': [
            '[data-test="detailSalary"]',
            'div.JobCard_salaryEstimate__arV5J',
            'span.salary-estimate',
            'div.salary'
        ],
        'rating': [
            'span[data-test="rating"]',
            'span.rating',
            'div.EmployerProfile_ratingContainer__ul0Ef span'
        ],
        'job_description': [
            'div.JobDetails_jobDescription__uW_fK',
            'div[class*="jobDescriptionContent"]',
            'div.jobDescriptionContent',
            'div[class*="description"]'
        ]
    }
    
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None, headless: bool = True):
        self.email = email
        self.password = password
        self.jobs = []
        self.failed_jobs = []
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, 15)
        self.short_wait = WebDriverWait(self.driver, 5)
    
    def _init_driver(self, headless: bool):
        """Initialize Chrome driver with anti-detection"""
        options = webdriver.ChromeOptions()
        
        if headless:
            options.add_argument('--headless=new')
        
        # Anti-detection measures
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        
        # Realistic user agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stealth options
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance optimizations
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Disable images for speed
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=options)
        
        # Additional anti-detection scripts
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
        return driver
    
    def _human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Add random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _find_element_by_selectors(self, parent, selectors: List[str], timeout: int = 5):
        """Try multiple selectors to find an element"""
        for selector in selectors:
            try:
                if timeout > 0:
                    element = WebDriverWait(parent, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                else:
                    element = parent.find_element(By.CSS_SELECTOR, selector)
                return element
            except (TimeoutException, NoSuchElementException):
                continue
        return None
    
    def _extract_text(self, parent, selectors: List[str], default: str = "") -> str:
        """Extract text using multiple selectors"""
        element = self._find_element_by_selectors(parent, selectors, timeout=0)
        return element.text.strip() if element else default
    
    def _close_popups(self):
        """Close any popup dialogs or modals"""
        popup_selectors = [
            "button.modal_closeIcon",
            "button[data-test='modal-close-button']",
            "button[aria-label='Close']",
            "button.CloseButton",
            "svg.SVGInline-svg",
            "[data-test='close-popup']"
        ]
        
        for selector in popup_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    try:
                        if btn.is_displayed():
                            btn.click()
                            self._human_delay(0.5, 1.0)
                    except:
                        pass
            except:
                pass
        
        # Handle overlays
        try:
            overlays = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='overlay'], div[class*='modal']")
            for overlay in overlays:
                try:
                    self.driver.execute_script("arguments[0].remove();", overlay)
                except:
                    pass
        except:
            pass
    
    def login(self) -> bool:
        """Login to Glassdoor (optional but provides better access)"""
        if not self.email or not self.password:
            logger.info("⚠️  No credentials provided. Continuing without login.")
            return True
        
        try:
            logger.info("🔐 Logging into Glassdoor...")
            self.driver.get(f"{self.BASE_URL}/profile/login_input.htm")
            self._human_delay(2, 4)
            
            self._close_popups()
            
            # Try email input
            email_selectors = ["#inlineUserEmail", "input[name='username']", "input[type='email']"]
            email_field = self._find_element_by_selectors(self.driver, email_selectors)
            
            if email_field:
                # Human-like typing
                for char in self.email:
                    email_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                self._human_delay(0.5, 1.0)
                
                # Click continue/next button
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    submit_btn.click()
                    self._human_delay(1, 2)
                except:
                    pass
            
            # Enter password
            password_selectors = ["#inlineUserPassword", "input[name='password']", "input[type='password']"]
            password_field = self._find_element_by_selectors(self.driver, password_selectors)
            
            if password_field:
                for char in self.password:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                self._human_delay(0.5, 1.0)
                
                # Submit login
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_btn.click()
                self._human_delay(3, 5)
            
            # Check login success
            if "member" in self.driver.current_url or "job" in self.driver.current_url:
                logger.info("✅ Login successful")
                return True
            else:
                logger.warning("⚠️  Login may have failed. Continuing anyway...")
                return True
                
        except Exception as e:
            logger.warning(f"Login error: {str(e)}. Continuing without login...")
            return True
    
    def search_jobs(self, 
                   keywords: str,
                   location: str = "London, England",
                   max_results: int = 100,
                   job_type: Optional[str] = None,
                   salary_min: Optional[int] = None,
                   company_rating_min: Optional[float] = None,
                   experience_level: Optional[str] = None,
                   remote_only: bool = False) -> List[Dict]:
        """
        Search for jobs on Glassdoor
        
        Args:
            keywords: Job title or keywords
            location: Location string
            max_results: Maximum results to return
            job_type: fulltime, contract, parttime, temporary, internship
            salary_min: Minimum salary filter
            company_rating_min: Minimum company rating (1-5)
            experience_level: entry, mid, senior, director, executive
            remote_only: Filter for remote jobs only
        """
        logger.info(f"🔍 Searching Glassdoor: '{keywords}' in '{location}'")
        logger.info(f"   Target: {max_results} jobs")
        
        # Build search URL with filters
        search_url = self._build_search_url(
            keywords, location, job_type, salary_min, 
            company_rating_min, experience_level, remote_only
        )
        
        try:
            self.driver.get(search_url)
            self._human_delay(3, 5)
            self._close_popups()
            
            page = 1
            jobs_collected = 0
            consecutive_failures = 0
            max_consecutive_failures = 3
            
            while jobs_collected < max_results and consecutive_failures < max_consecutive_failures:
                logger.info(f"📄 Processing page {page}...")
                
                self._human_delay(2, 4)
                self._close_popups()
                
                # Scroll to load lazy content
                self._scroll_page()
                
                # Find job cards with retry
                job_cards = self._find_job_cards()
                
                if not job_cards:
                    logger.warning(f"No job cards found on page {page}")
                    consecutive_failures += 1
                    
                    # Try scrolling more
                    self._scroll_page(slow=True)
                    self._human_delay(2, 3)
                    job_cards = self._find_job_cards()
                    
                    if not job_cards:
                        logger.info("Still no jobs found. Moving to next page or stopping...")
                        if not self._go_to_next_page():
                            break
                        page += 1
                        continue
                
                consecutive_failures = 0
                logger.info(f"   Found {len(job_cards)} job cards")
                
                # Parse jobs with retry logic
                for i, card in enumerate(job_cards):
                    if jobs_collected >= max_results:
                        break
                    
                    try:
                        # Scroll card into view
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                            card
                        )
                        self._human_delay(0.3, 0.7)
                        
                        # Try to parse the job
                        job_data = self._parse_job_card(card, retry=True)
                        
                        if job_data:
                            # Apply filters
                            if self._passes_filters(job_data, company_rating_min):
                                self.jobs.append(job_data)
                                jobs_collected += 1
                                logger.info(f"   ✓ [{jobs_collected}/{max_results}] {job_data['title']} @ {job_data['company']}")
                        else:
                            self.failed_jobs.append(f"Page {page}, Card {i+1}")
                    
                    except StaleElementReferenceException:
                        logger.debug(f"Stale element on card {i+1}, skipping...")
                        continue
                    except Exception as e:
                        logger.debug(f"Error on card {i+1}: {str(e)}")
                        continue
                
                # Navigate to next page
                if jobs_collected < max_results:
                    if not self._go_to_next_page():
                        logger.info("No more pages available")
                        break
                    page += 1
                    self._human_delay(2, 4)
            
            logger.info(f"✅ Collected {len(self.jobs)} jobs from Glassdoor")
            if self.failed_jobs:
                logger.warning(f"⚠️  Failed to parse {len(self.failed_jobs)} job cards")
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return self.jobs
    
    def _build_search_url(self, keywords: str, location: str, job_type: Optional[str] = None,
                          salary_min: Optional[int] = None, company_rating_min: Optional[float] = None,
                          experience_level: Optional[str] = None, remote_only: bool = False) -> str:
        """Build Glassdoor search URL with filters"""
        
        params = [
            f"sc.keyword={quote(keywords)}",
            "locT=C",
            f"locKeyword={quote(location)}"
        ]
        
        # Job type filter
        if job_type:
            type_map = {
                'fulltime': 'FULLTIME',
                'parttime': 'PARTTIME',
                'contract': 'CONTRACT',
                'temporary': 'TEMPORARY',
                'internship': 'INTERNSHIP'
            }
            if job_type.lower() in type_map:
                params.append(f"jobType={type_map[job_type.lower()]}")
        
        # Experience level
        if experience_level:
            level_map = {
                'entry': 'ENTRY_LEVEL',
                'mid': 'MID_SENIOR_LEVEL',
                'senior': 'MID_SENIOR_LEVEL',
                'director': 'DIRECTOR',
                'executive': 'EXECUTIVE'
            }
            if experience_level.lower() in level_map:
                params.append(f"seniorityType={level_map[experience_level.lower()]}")
        
        # Remote filter
        if remote_only:
            params.append("remoteWorkType=1")
        
        # Salary minimum
        if salary_min:
            params.append(f"minSalary={salary_min}")
        
        return f"{self.JOBS_URL}?{'&'.join(params)}"
    
    def _scroll_page(self, slow: bool = False):
        """Scroll page to load lazy content"""
        if slow:
            # Slow scroll to bottom
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(0, total_height, 300):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.2)
        else:
            # Quick scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            self._human_delay(0.5, 1.0)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._human_delay(0.5, 1.0)
    
    def _find_job_cards(self) -> List:
        """Find job cards using multiple strategies"""
        job_cards = []
        
        for selector in self.SELECTORS['job_card']:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    job_cards = cards
                    break
            except:
                continue
        
        return job_cards
    
    def _passes_filters(self, job: Dict, rating_min: Optional[float]) -> bool:
        """Check if job passes minimum filters"""
        if rating_min and job.get('company_rating'):
            try:
                rating = float(job['company_rating'])
                if rating < rating_min:
                    return False
            except ValueError:
                pass
        
        return True
    
    def _go_to_next_page(self) -> bool:
        """Navigate to next page of results"""
        next_selectors = [
            "button[data-test='pagination-next']",
            "a[data-test='pagination-next']",
            "button[aria-label='Next']",
            "a.next",
            "button.nextButton"
        ]
        
        for selector in next_selectors:
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                if next_button and next_button.is_enabled() and next_button.is_displayed():
                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    self._human_delay(0.5, 1.0)
                    
                    # Click with retry
                    try:
                        next_button.click()
                    except:
                        # Try JavaScript click
                        self.driver.execute_script("arguments[0].click();", next_button)
                    
                    return True
            except:
                continue
        
        logger.debug("Could not find next button")
        return False
    
    def _parse_job_card(self, card, retry: bool = True) -> Optional[Dict]:
        """Parse individual job card with retry logic"""
        max_retries = 2 if retry else 1
        
        for attempt in range(max_retries):
            try:
                # Click card to load details (may help with lazy loading)
                try:
                    ActionChains(self.driver).move_to_element(card).pause(0.2).perform()
                    card.click()
                    self._human_delay(1, 2)
                except:
                    pass
                
                # Extract data using flexible selectors
                title = self._extract_text(card, self.SELECTORS['job_title'])
                company = self._extract_text(card, self.SELECTORS['company_name'])
                location = self._extract_text(card, self.SELECTORS['location'])
                salary = self._extract_text(card, self.SELECTORS['salary'])
                rating = self._extract_text(card, self.SELECTORS['rating'])
                
                # Extract job URL and ID
                job_url = ""
                job_id = ""
                try:
                    link = card.find_element(By.CSS_SELECTOR, "a[href*='job-listing']")
                    job_url = link.get_attribute('href')
                    
                    # Extract job ID from URL
                    match = re.search(r'jobListingId=(\d+)', job_url)
                    if not match:
                        match = re.search(r'/(\d+)\?', job_url)
                    if match:
                        job_id = match.group(1)
                except:
                    pass
                
                # Extract posted date
                posted_date = ""
                try:
                    date_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-age']")
                    posted_date = date_elem.text.strip()
                except:
                    pass
                
                # Must have at minimum title and company
                if not title or not company:
                    if attempt < max_retries - 1:
                        self._human_delay(1, 2)
                        continue
                    return None
                
                # Build job data
                job_data = {
                    'id': job_id or f"glassdoor_{hash(title + company)}",
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'company_rating': rating,
                    'url': job_url,
                    'posted_date': posted_date,
                    'source': 'glassdoor',
                    'scraped_at': datetime.now().isoformat()
                }
                
                return job_data
                
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    logger.debug(f"Stale element, retry {attempt + 1}/{max_retries}")
                    self._human_delay(1, 2)
                    continue
                return None
            except Exception as e:
                logger.debug(f"Error parsing job card (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    self._human_delay(1, 2)
                    continue
                return None
        
        return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Get full job details including description"""
        try:
            logger.debug(f"Fetching job details: {job_url}")
            self.driver.get(job_url)
            self._human_delay(2, 4)
            self._close_popups()
            
            details = {}
            
            # Full job description
            desc_element = self._find_element_by_selectors(
                self.driver, 
                self.SELECTORS['job_description']
            )
            if desc_element:
                details['full_description'] = desc_element.text.strip()
            
            # Company info
            try:
                # Company size
                size_xpath = "//div[contains(text(), 'Size')]/following-sibling::div"
                size_elem = self.driver.find_element(By.XPATH, size_xpath)
                details['company_size'] = size_elem.text.strip()
            except:
                pass
            
            try:
                # Industry
                industry_xpath = "//div[contains(text(), 'Industry')]/following-sibling::div"
                industry_elem = self.driver.find_element(By.XPATH, industry_xpath)
                details['industry'] = industry_elem.text.strip()
            except:
                pass
            
            try:
                # Revenue
                revenue_xpath = "//div[contains(text(), 'Revenue')]/following-sibling::div"
                revenue_elem = self.driver.find_element(By.XPATH, revenue_xpath)
                details['company_revenue'] = revenue_elem.text.strip()
            except:
                pass
            
            # Benefits
            try:
                benefits = []
                benefit_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='benefit']")
                for elem in benefit_elements:
                    benefits.append(elem.text.strip())
                if benefits:
                    details['benefits'] = benefits
            except:
                pass
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching job details: {str(e)}")
            return None
    
    def enrich_jobs_with_details(self, max_jobs: int = 10):
        """Fetch full details for top jobs"""
        logger.info(f"📝 Enriching top {min(max_jobs, len(self.jobs))} jobs with full details...")
        
        enriched = 0
        for i, job in enumerate(self.jobs[:max_jobs]):
            if job.get('url'):
                logger.info(f"   [{i+1}/{min(max_jobs, len(self.jobs))}] {job['title']}")
                details = self.get_job_details(job['url'])
                if details:
                    job.update(details)
                    enriched += 1
                self._human_delay(2, 4)
        
        logger.info(f"✅ Enriched {enriched} jobs with full details")
    
    def save_jobs(self, filename: str = 'glassdoor_jobs.json', format: str = 'json'):
        """Save scraped jobs to file"""
        if format == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        elif format == 'csv':
            import csv
            if filename.endswith('.json'):
                filename = filename.replace('.json', '.csv')
            
            if self.jobs:
                keys = self.jobs[0].keys()
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(self.jobs)
        
        logger.info(f"💾 Saved {len(self.jobs)} jobs to {filename}")
    
    def print_summary(self):
        """Print scraping summary with statistics"""
        if not self.jobs:
            logger.warning("No jobs to summarize")
            return
        
        print("\n" + "="*70)
        print("📊 GLASSDOOR SCRAPING SUMMARY")
        print("="*70)
        
        print(f"\n📈 Overall Stats:")
        print(f"   Total Jobs Collected: {len(self.jobs)}")
        print(f"   Failed Parses: {len(self.failed_jobs)}")
        print(f"   Success Rate: {len(self.jobs)/(len(self.jobs)+len(self.failed_jobs))*100:.1f}%")
        
        print(f"\n🏢 Companies:")
        unique_companies = set(j['company'] for j in self.jobs if j.get('company'))
        print(f"   Unique Companies: {len(unique_companies)}")
        
        company_counts = {}
        for job in self.jobs:
            comp = job.get('company', 'Unknown')
            company_counts[comp] = company_counts.get(comp, 0) + 1
        
        print(f"   Top Companies:")
        for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      • {company}: {count} jobs")
        
        print(f"\n📍 Locations:")
        unique_locations = set(j['location'] for j in self.jobs if j.get('location'))
        print(f"   Unique Locations: {len(unique_locations)}")
        
        print(f"\n💰 Salary Information:")
        with_salary = sum(1 for j in self.jobs if j.get('salary'))
        print(f"   Jobs with Salary: {with_salary} ({with_salary/len(self.jobs)*100:.1f}%)")
        
        print(f"\n⭐ Company Ratings:")
        with_rating = sum(1 for j in self.jobs if j.get('company_rating'))
        print(f"   Jobs with Rating: {with_rating} ({with_rating/len(self.jobs)*100:.1f}%)")
        
        if with_rating > 0:
            ratings = []
            for j in self.jobs:
                if j.get('company_rating'):
                    try:
                        rating = float(j['company_rating'])
                        ratings.append(rating)
                    except ValueError:
                        pass
            
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                print(f"   Average Rating: {avg_rating:.2f}/5.0")
                print(f"   Rating Range: {min(ratings):.1f} - {max(ratings):.1f}")
        
        print("\n" + "="*70 + "\n")
    
    def close(self):
        """Close browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Browser closed")
            except:
                pass


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Glassdoor Job Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python glassdoor_scraper.py -k "data scientist" -l "London, England" -m 50
  
  # Remote full-time jobs with rating filter
  python glassdoor_scraper.py -k "software engineer" --remote --job-type fulltime --rating-min 4.0
  
  # With enrichment
  python glassdoor_scraper.py -k "product manager" -m 30 --enrich 10
  
  # With credentials for better access
  python glassdoor_scraper.py -e your@email.com -p password -k "data analyst"
        """
    )
    
    # Authentication
    parser.add_argument('--email', '-e', help='Glassdoor email', default=os.getenv('GLASSDOOR_EMAIL'))
    parser.add_argument('--password', '-p', help='Glassdoor password', default=os.getenv('GLASSDOOR_PASSWORD'))
    
    # Search parameters
    parser.add_argument('--keywords', '-k', required=True, help='Job keywords to search')
    parser.add_argument('--location', '-l', default='London, England', help='Job location')
    parser.add_argument('--max-results', '-m', type=int, default=50, help='Maximum number of jobs to collect')
    
    # Filters
    parser.add_argument('--job-type', choices=['fulltime', 'parttime', 'contract', 'temporary', 'internship'],
                       help='Job type filter')
    parser.add_argument('--salary-min', type=int, help='Minimum salary (annual)')
    parser.add_argument('--rating-min', type=float, help='Minimum company rating (1-5)')
    parser.add_argument('--experience', choices=['entry', 'mid', 'senior', 'director', 'executive'],
                       help='Experience level')
    parser.add_argument('--remote', action='store_true', help='Remote jobs only')
    
    # Enrichment
    parser.add_argument('--enrich', type=int, default=0, 
                       help='Number of top jobs to enrich with full details')
    
    # Output
    parser.add_argument('--output', '-o', default='glassdoor_jobs.json', help='Output filename')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json', help='Output format')
    
    # Display
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--show-browser', action='store_true', help='Show browser window')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = GlassdoorScraper(
        email=args.email,
        password=args.password,
        headless=args.headless and not args.show_browser
    )
    
    try:
        # Login if credentials provided
        if args.email and args.password:
            scraper.login()
        
        # Search jobs
        jobs = scraper.search_jobs(
            keywords=args.keywords,
            location=args.location,
            max_results=args.max_results,
            job_type=args.job_type,
            salary_min=args.salary_min,
            company_rating_min=args.rating_min,
            experience_level=args.experience,
            remote_only=args.remote
        )
        
        # Enrich with details if requested
        if args.enrich > 0 and jobs:
            scraper.enrich_jobs_with_details(max_jobs=args.enrich)
        
        # Save results
        if jobs:
            scraper.save_jobs(filename=args.output, format=args.format)
            scraper.print_summary()
        else:
            logger.warning("⚠️  No jobs were collected")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
