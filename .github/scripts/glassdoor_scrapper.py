#!/usr/bin/env python3
"""
Glassdoor Job Scraper
Enhanced scraping with company reviews and ratings
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
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GlassdoorScraper:
    """Glassdoor job scraper with company ratings"""
    
    BASE_URL = "https://www.glassdoor.co.uk"
    JOBS_URL = f"{BASE_URL}/Job/jobs.htm"
    
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None, headless: bool = True):
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
        options.add_argument('--window-size=1920,1080')
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def login(self) -> bool:
        """Login to Glassdoor (optional but recommended)"""
        if not self.email or not self.password:
            logger.info("⚠️  No credentials provided. Proceeding without login (limited access).")
            return True
        
        try:
            logger.info("🔐 Logging into Glassdoor...")
            self.driver.get(f"{self.BASE_URL}/profile/login_input.htm")
            time.sleep(3)
            
            # Close any popups
            self._close_popups()
            
            # Enter email
            try:
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "inlineUserEmail"))
                )
                email_field.send_keys(self.email)
                
                # Click continue
                continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                continue_btn.click()
                time.sleep(2)
            except:
                # Try alternative login form
                email_field = self.driver.find_element(By.NAME, "username")
                email_field.send_keys(self.email)
            
            # Enter password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "inlineUserPassword"))
            )
            password_field.send_keys(self.password)
            
            # Click sign in
            signin_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            signin_btn.click()
            
            time.sleep(5)
            
            # Check if login successful
            if "member" in self.driver.current_url or "job" in self.driver.current_url:
                logger.info("✅ Login successful")
                return True
            else:
                logger.warning("⚠️  Login may have failed. Continuing anyway...")
                return True
                
        except Exception as e:
            logger.warning(f"Login error: {str(e)}. Continuing without login...")
            return True
    
    def _close_popups(self):
        """Close any popup dialogs"""
        try:
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.modal_closeIcon, button[data-test='modal-close-button']")
            for btn in close_buttons:
                try:
                    btn.click()
                    time.sleep(0.5)
                except:
                    pass
        except:
            pass
    
    def search_jobs(self, 
                   keywords: str,
                   location: str = "London, England",
                   max_results: int = 100,
                   job_type: Optional[str] = None,
                   salary_min: Optional[int] = None,
                   company_rating_min: Optional[float] = None) -> List[Dict]:
        """
        Search for jobs on Glassdoor
        
        Args:
            keywords: Job title or keywords
            location: Location string
            max_results: Maximum results to return
            job_type: fulltime, contract, parttime, temporary, internship
            salary_min: Minimum salary filter
            company_rating_min: Minimum company rating (1-5)
        """
        logger.info(f"🔍 Searching Glassdoor for: {keywords} in {location}")
        
        # Build search URL
        search_url = self._build_search_url(keywords, location)
        
        try:
            self.driver.get(search_url)
            time.sleep(4)
            
            # Close any popups
            self._close_popups()
            
            # Apply filters if specified
            if job_type or salary_min or company_rating_min:
                self._apply_filters(job_type, salary_min, company_rating_min)
            
            page = 1
            jobs_collected = 0
            
            while jobs_collected < max_results:
                logger.info(f"Processing page {page}...")
                
                # Wait for job listings to load
                time.sleep(3)
                self._close_popups()
                
                # Find job cards
                job_cards = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "li[data-test='jobListing'], article.job-listing, li.react-job-listing"
                )
                
                if not job_cards:
                    logger.info("No job cards found on this page")
                    break
                
                logger.info(f"Found {len(job_cards)} job cards")
                
                # Parse jobs
                for i, card in enumerate(job_cards):
                    if jobs_collected >= max_results:
                        break
                    
                    # Scroll card into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    time.sleep(0.5)
                    
                    job_data = self._parse_job_card(card)
                    if job_data:
                        self.jobs.append(job_data)
                        jobs_collected += 1
                        logger.info(f"Progress: {jobs_collected}/{max_results} - {job_data['title']}")
                
                # Try to go to next page
                if jobs_collected < max_results:
                    if not self._go_to_next_page():
                        logger.info("No more pages available")
                        break
                    page += 1
                    time.sleep(3)
                else:
                    break
            
            logger.info(f"✅ Collected {len(self.jobs)} jobs from Glassdoor")
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
        
        return self.jobs
    
    def _build_search_url(self, keywords: str, location: str) -> str:
        """Build Glassdoor search URL"""
        from urllib.parse import quote
        
        return f"{self.JOBS_URL}?sc.keyword={quote(keywords)}&locT=C&locId=&locKeyword={quote(location)}"
    
    def _apply_filters(self, job_type: Optional[str], salary_min: Optional[int], company_rating_min: Optional[float]):
        """Apply search filters"""
        try:
            # Job type filter
            if job_type:
                logger.info(f"Applying job type filter: {job_type}")
                # Click filters button
                try:
                    filters_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-test='filtersButton']")
                    filters_btn.click()
                    time.sleep(1)
                except:
                    pass
            
            # Note: Glassdoor's filter UI changes frequently
            # These selectors may need updating
            
        except Exception as e:
            logger.warning(f"Could not apply filters: {str(e)}")
    
    def _go_to_next_page(self) -> bool:
        """Navigate to next page of results"""
        try:
            # Find next button
            next_button = self.driver.find_element(
                By.CSS_SELECTOR,
                "button[data-test='pagination-next'], a[data-test='pagination-next']"
            )
            
            if next_button and next_button.is_enabled():
                next_button.click()
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Could not find next button: {str(e)}")
            return False
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse individual job card"""
        try:
            # Click card to load details
            try:
                card.click()
                time.sleep(2)
            except:
                pass
            
            # Job title
            title = ""
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "a[data-test='job-link'], a.job-title")
                title = title_elem.text.strip()
            except:
                pass
            
            # Company name
            company = ""
            try:
                company_elem = card.find_element(By.CSS_SELECTOR, "[data-test='employer-name'], span.employer-name")
                company = company_elem.text.strip()
            except:
                pass
            
            # Location
            location = ""
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, "[data-test='emp-location'], span.location")
                location = location_elem.text.strip()
            except:
                pass
            
            # Salary
            salary = ""
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, "[data-test='detailSalary'], span.salary-estimate")
                salary = salary_elem.text.strip()
            except:
                pass
            
            # Company rating
            rating = ""
            try:
                rating_elem = card.find_element(By.CSS_SELECTOR, "span.rating, [data-test='rating']")
                rating = rating_elem.text.strip()
            except:
                pass
            
            # Job age (posted date)
            posted_date = ""
            try:
                date_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-age'], div.job-age")
                posted_date = date_elem.text.strip()
            except:
                pass
            
            # Job description (brief)
            description = ""
            try:
                desc_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-description'], div.job-description")
                description = desc_elem.text.strip()
            except:
                pass
            
            # Job URL
            job_url = ""
            job_id = ""
            try:
                link = card.find_element(By.CSS_SELECTOR, "a[data-test='job-link']")
                job_url = link.get_attribute('href')
                
                # Extract job ID from URL
                match = re.search(r'jobListingId=(\d+)', job_url)
                if match:
                    job_id = match.group(1)
            except:
                pass
            
            if not title or not company:
                return None
            
            job_data = {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'company_rating': rating,
                'description_snippet': description,
                'url': job_url,
                'posted_date': posted_date,
                'source': 'glassdoor',
                'scraped_at': datetime.now().isoformat()
            }
            
            return job_data
            
        except Exception as e:
            logger.debug(f"Error parsing job card: {str(e)}")
            return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Get full job details including description"""
        try:
            logger.debug(f"Fetching job details: {job_url}")
            self.driver.get(job_url)
            time.sleep(3)
            
            self._close_popups()
            
            details = {}
            
            # Full job description
            try:
                desc_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobDescriptionContent, div[class*='description']"))
                )
                details['full_description'] = desc_elem.text.strip()
            except:
                pass
            
            # Company overview
            try:
                overview_elem = self.driver.find_element(By.CSS_SELECTOR, "div.companyOverview, div[class*='overview']")
                details['company_overview'] = overview_elem.text.strip()
            except:
                pass
            
            # Company size
            try:
                size_elem = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Size')]/following-sibling::div")
                details['company_size'] = size_elem.text.strip()
            except:
                pass
            
            # Industry
            try:
                industry_elem = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Industry')]/following-sibling::div")
                details['industry'] = industry_elem.text.strip()
            except:
                pass
            
            # Revenue
            try:
                revenue_elem = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Revenue')]/following-sibling::div")
                details['company_revenue'] = revenue_elem.text.strip()
            except:
                pass
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching job details: {str(e)}")
            return None
    
    def get_company_reviews(self, company_name: str) -> Optional[Dict]:
        """Get company reviews and ratings"""
        try:
            # Search for company
            search_url = f"{self.BASE_URL}/Reviews/{company_name.replace(' ', '-')}-Reviews-E"
            self.driver.get(search_url)
            time.sleep(3)
            
            reviews = {}
            
            # Overall rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "div.rating")
                reviews['overall_rating'] = rating_elem.text.strip()
            except:
                pass
            
            # Recommend to friend percentage
            try:
                recommend_elem = self.driver.find_element(By.CSS_SELECTOR, "div.recommendToFriend")
                reviews['recommend_percentage'] = recommend_elem.text.strip()
            except:
                pass
            
            # CEO approval
            try:
                ceo_elem = self.driver.find_element(By.CSS_SELECTOR, "div.ceoApproval")
                reviews['ceo_approval'] = ceo_elem.text.strip()
            except:
                pass
            
            # Rating breakdown
            try:
                ratings = {}
                rating_items = self.driver.find_elements(By.CSS_SELECTOR, "div.ratingItem")
                for item in rating_items:
                    category = item.find_element(By.CSS_SELECTOR, "div.category").text.strip()
                    value = item.find_element(By.CSS_SELECTOR, "div.rating").text.strip()
                    ratings[category] = value
                reviews['rating_breakdown'] = ratings
            except:
                pass
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error fetching company reviews: {str(e)}")
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
    
    def save_jobs(self, filename: str = 'glassdoor_jobs.json'):
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
        print("📊 GLASSDOOR SCRAPING SUMMARY")
        print("="*60)
        print(f"Total Jobs: {len(self.jobs)}")
        print(f"Unique Companies: {len(set(j['company'] for j in self.jobs if j.get('company')))}")
        print(f"Locations: {len(set(j['location'] for j in self.jobs if j.get('location')))}")
        
        with_salary = sum(1 for j in self.jobs if j.get('salary'))
        print(f"With Salary Info: {with_salary} ({with_salary/len(self.jobs)*100:.1f}%)")
        
        with_rating = sum(1 for j in self.jobs if j.get('company_rating'))
        print(f"With Company Rating: {with_rating} ({with_rating/len(self.jobs)*100:.1f}%)")
        
        if with_rating > 0:
            avg_rating = sum(float(j['company_rating']) for j in self.jobs if j.get('company_rating') and j['company_rating'].replace('.','').isdigit()) / with_rating
            print(f"Average Company Rating: {avg_rating:.1f}/5.0")
        
        print("="*60 + "\n")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")


def main():
    parser = argparse.ArgumentParser(description='Glassdoor Job Scraper')
    parser.add_argument('--email', '-e', help='Glassdoor email', default=os.getenv('GLASSDOOR_EMAIL'))
    parser.add_argument('--password', '-p', help='Glassdoor password', default=os.getenv('GLASSDOOR_PASSWORD'))
    parser.add_argument('--keywords', '-k', required=True, help='Job keywords to search')
    parser.add_argument('--location', '-l', default='London, England', help='Location')
    parser.add_argument('--max-results', '-m', type=int, default=50, help='Max results (default: 50)')
    parser.add_argument('--job-type', '-j', help='Job type (fulltime, contract, etc.)')
    parser.add_argument('--salary-min', '-s', type=int, help='Minimum salary')
    parser.add_argument('--rating-min', '-r', type=float, help='Minimum company rating (1-5)')
    parser.add_argument('--enrich', type=int, default=0, help='Enrich top N jobs with full details')
    parser.add_argument('--output', '-o', default='glassdoor_jobs.json', help='Output file')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    scraper = None
    try:
        # Initialize scraper
        scraper = GlassdoorScraper(args.email, args.password, headless=args.headless)
        
        # Login (optional)
        scraper.login()
        
        # Search jobs
        scraper.search_jobs(
            keywords=args.keywords,
            location=args.location,
            max_results=args.max_results,
            job_type=args.job_type,
            salary_min=args.salary_min,
            company_rating_min=args.rating_min
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
