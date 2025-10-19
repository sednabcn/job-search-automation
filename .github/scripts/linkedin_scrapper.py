#!/usr/bin/env python3
"""
LinkedIn Job Scraper
Advanced scraping with authentication and job search
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import random
from datetime import datetime
from typing import List, Dict, Optional
import logging
import argparse
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    """LinkedIn job scraper with authentication"""
    
    BASE_URL = "https://www.linkedin.com"
    JOBS_URL = f"{BASE_URL}/jobs/search/"
    
    def __init__(self, email: str, password: str, headless: bool = True):
        self.email = email
        self.password = password
        self.jobs = []
        self.driver = self._init_driver(headless)
    
    def _init_driver(self, headless: bool):
        """Initialize Chrome driver"""
        options = webdriver.ChromeOptions()
        
        if headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            logger.info("🔐 Logging into LinkedIn...")
            self.driver.get(f"{self.BASE_URL}/login")
            time.sleep(2)
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            
            # Click login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            # Check if login successful
            if "feed" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                logger.info("✅ Login successful")
                
                # Handle verification if needed
                if "checkpoint" in self.driver.current_url:
                    logger.warning("⚠️  Verification required. Please complete manually.")
                    input("Press Enter after completing verification...")
                
                return True
            else:
                logger.error("❌ Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def search_jobs(self, 
                   keywords: str,
                   location: str = "London, England, United Kingdom",
                   max_results: int = 100,
                   job_type: Optional[str] = None,
                   experience_level: Optional[str] = None,
                   remote: bool = False,
                   posted_within: Optional[str] = None) -> List[Dict]:
        """
        Search for jobs on LinkedIn
        
        Args:
            keywords: Job title or keywords
            location: Location string
            max_results: Maximum results to return
            job_type: F (Full-time), C (Contract), P (Part-time), T (Temporary), I (Internship)
            experience_level: 1 (Entry), 2 (Associate), 3 (Mid-Senior), 4 (Director), 5 (Executive)
            remote: Filter remote jobs
            posted_within: r86400 (24h), r604800 (week), r2592000 (month)
        """
        logger.info(f"🔍 Searching LinkedIn for: {keywords} in {location}")
        
        # Build search URL
        search_url = self._build_search_url(
            keywords, location, job_type, 
            experience_level, remote, posted_within
        )
        
        try:
            self.driver.get(search_url)
            time.sleep(3)
            
            # Scroll and load all jobs
            jobs_collected = 0
            scroll_attempts = 0
            max_scrolls = 20
            
            while jobs_collected < max_results and scroll_attempts < max_scrolls:
                # Find job cards
                job_cards = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "div.job-card-container, li.jobs-search-results__list-item"
                )
                
                logger.info(f"Found {len(job_cards)} job cards on page")
                
                # Parse new jobs
                for card in job_cards[jobs_collected:]:
                    if jobs_collected >= max_results:
                        break
                    
                    job_data = self._parse_job_card(card)
                    if job_data and job_data not in self.jobs:
                        self.jobs.append(job_data)
                        jobs_collected += 1
                
                logger.info(f"Progress: {jobs_collected}/{max_results} jobs")
                
                # Scroll to load more
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
                
                # Try to click "See more jobs" button
                try:
                    see_more = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button.infinite-scroller__show-more-button"
                    )
                    see_more.click()
                    time.sleep(2)
                except:
                    pass
                
                scroll_attempts += 1
            
            logger.info(f"✅ Collected {len(self.jobs)} jobs from LinkedIn")
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
        
        return self.jobs
    
    def _build_search_url(self, keywords: str, location: str, 
                         job_type: Optional[str], experience_level: Optional[str],
                         remote: bool, posted_within: Optional[str]) -> str:
        """Build LinkedIn jobs search URL"""
        from urllib.parse import quote
        
        url = f"{self.JOBS_URL}?keywords={quote(keywords)}&location={quote(location)}"
        
        if job_type:
            url += f"&f_JT={job_type}"
        if experience_level:
            url += f"&f_E={experience_level}"
        if remote:
            url += "&f_WT=2"  # Remote filter
        if posted_within:
            url += f"&f_TPR={posted_within}"
        
        return url
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse individual job card"""
        try:
            # Click card to load details
            try:
                card.click()
                time.sleep(1)
            except:
                pass
            
            # Job title
            title_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title, h3.job-card-list__title")
            job_title = title_elem.text.strip() if title_elem else ""
            
            # Job URL and ID
            job_url = ""
            job_id = ""
            try:
                job_link = card.find_element(By.CSS_SELECTOR, "a[data-job-id], a.job-card-container__link")
                job_url = job_link.get_attribute('href') if job_link else ""
                job_id = job_link.get_attribute('data-job-id') if job_link else ""
            except:
                pass
            
            # Company name
            company = ""
            try:
                company_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-container__company-name, h4.job-card-container__company-name")
                company = company_elem.text.strip()
            except:
                pass
            
            # Location
            location = ""
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, "li.job-card-container__metadata-item, span.job-card-container__metadata-item")
                location = location_elem.text.strip()
            except:
                pass
            
            # Salary (if available)
            salary = ""
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, "span.job-card-container__salary")
                salary = salary_elem.text.strip()
            except:
                pass
            
            # Posted date
            posted_date = ""
            try:
                date_elem = card.find_element(By.CSS_SELECTOR, "time")
                posted_date = date_elem.get_attribute('datetime') or date_elem.text.strip()
            except:
                pass
            
            if not job_title:
                return None
            
            job_data = {
                'id': job_id,
                'title': job_title,
                'company': company,
                'location': location,
                'salary': salary,
                'url': job_url,
                'posted_date': posted_date,
                'source': 'linkedin',
                'scraped_at': datetime.now().isoformat()
            }
            
            return job_data
            
        except Exception as e:
            logger.debug(f"Error parsing job card: {str(e)}")
            return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Get full job details from job page"""
        try:
            logger.debug(f"Fetching job details: {job_url}")
            self.driver.get(job_url)
            time.sleep(3)
            
            details = {}
            
            # Full job description
            try:
                desc_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-description, div.jobs-description__content"))
                )
                details['full_description'] = desc_elem.text.strip()
            except:
                pass
            
            # Seniority level
            try:
                seniority = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Seniority level')]/following-sibling::span")
                details['seniority_level'] = seniority.text.strip()
            except:
                pass
            
            # Employment type
            try:
                emp_type = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Employment type')]/following-sibling::span")
                details['employment_type'] = emp_type.text.strip()
            except:
                pass
            
            # Job function
            try:
                job_func = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Job function')]/following-sibling::span")
                details['job_function'] = job_func.text.strip()
            except:
                pass
            
            # Industries
            try:
                industries = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Industries')]/following-sibling::span")
                details['industries'] = industries.text.strip()
            except:
                pass
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching job details: {str(e)}")
            return None
    
    def enrich_jobs_with_details(self, max_jobs: int = 10):
        """Fetch full details for top jobs"""
        logger.info(f"Enriching {min(max_jobs, len(self.jobs))} jobs with full details...")
        
        for i, job in enumerate(self.jobs[:max_jobs]):
            if job.get('url'):
                logger.info(f"Fetching details {i+1}/{min(max_jobs, len(self.jobs))}: {job['title']}")
                details = self.get_job_details(job['url'])
                if details:
                    job.update(details)
                time.sleep(random.uniform(2, 4))
    
    def save_jobs(self, filename: str = 'linkedin_jobs.json'):
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
        print("📊 LINKEDIN SCRAPING SUMMARY")
        print("="*60)
        print(f"Total Jobs: {len(self.jobs)}")
        print(f"Unique Companies: {len(set(j['company'] for j in self.jobs if j.get('company')))}")
        print(f"Locations: {len(set(j['location'] for j in self.jobs if j.get('location')))}")
        
        with_salary = sum(1 for j in self.jobs if j.get('salary'))
        print(f"With Salary Info: {with_salary} ({with_salary/len(self.jobs)*100:.1f}%)")
        
        print("="*60 + "\n")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")


def main():
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper')
    parser.add_argument('--email', '-e', help='LinkedIn email', default=os.getenv('LINKEDIN_EMAIL'))
    parser.add_argument('--password', '-p', help='LinkedIn password', default=os.getenv('LINKEDIN_PASSWORD'))
    parser.add_argument('--keywords', '-k', required=True, help='Job keywords to search')
    parser.add_argument('--location', '-l', default='London, England, United Kingdom', help='Location')
    parser.add_argument('--max-results', '-m', type=int, default=50, help='Max results (default: 50)')
    parser.add_argument('--job-type', '-j', choices=['F', 'C', 'P', 'T', 'I'], help='Job type (F=Full-time, C=Contract, etc.)')
    parser.add_argument('--experience', '-x', choices=['1', '2', '3', '4', '5'], help='Experience level (1=Entry, 5=Executive)')
    parser.add_argument('--remote', action='store_true', help='Remote jobs only')
    parser.add_argument('--posted-within', choices=['r86400', 'r604800', 'r2592000'], help='Posted within (24h, week, month)')
    parser.add_argument('--enrich', type=int, default=0, help='Enrich top N jobs with full details')
    parser.add_argument('--output', '-o', default='linkedin_jobs.json', help='Output file')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    if not args.email or not args.password:
        logger.error("Email and password required. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD env vars or use --email and --password")
        return
    
    scraper = None
    try:
        # Initialize scraper
        scraper = LinkedInScraper(args.email, args.password, headless=args.headless)
        
        # Login
        if not scraper.login():
            logger.error("Failed to login. Exiting.")
            return
        
        # Search jobs
        scraper.search_jobs(
            keywords=args.keywords,
            location=args.location,
            max_results=args.max_results,
            job_type=args.job_type,
            experience_level=args.experience,
            remote=args.remote,
            posted_within=args.posted_within
        )
        
        # Enrich with details
        if args.enrich > 0:
            scraper.enrich_jobs_with_details(args.enrich)
        
        # Save and print summary
        scraper.save_jobs(args.output)
        scraper.print_summary()
        
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()
