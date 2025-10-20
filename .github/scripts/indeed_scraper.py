#!/usr/bin/env python3
"""
Indeed Job Scraper
Scrapes job listings from Indeed UK with advanced filtering and keyword extraction
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from urllib.parse import urlencode, quote_plus
import logging
from typing import List, Dict, Optional
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndeedScraper:
    """Scraper for Indeed UK job listings"""
    
    BASE_URL = "https://uk.indeed.com"
    
    def __init__(self, headless: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.jobs = []
    
    def search_jobs(self, 
                   job_title: str, 
                   location: str = "London", 
                   max_results: int = 100,
                   job_type: Optional[str] = None,
                   salary_min: Optional[int] = None) -> List[Dict]:
        """
        Search for jobs on Indeed
        
        Args:
            job_title: Job title to search for
            location: Location (default: London)
            max_results: Maximum number of results to return
            job_type: fulltime, contract, temporary, parttime
            salary_min: Minimum salary
        """
        logger.info(f"Searching Indeed for: {job_title} in {location}")
        
        start = 0
        page = 0
        
        while len(self.jobs) < max_results:
            params = {
                'q': job_title,
                'l': location,
                'start': start,
            }
            
            if job_type:
                params['jt'] = job_type
            
            if salary_min:
                params['salary'] = str(salary_min)
            
            url = f"{self.BASE_URL}/jobs?{urlencode(params)}"
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                if not job_cards:
                    logger.info("No more jobs found")
                    break
                
                for card in job_cards:
                    if len(self.jobs) >= max_results:
                        break
                    
                    job_data = self._parse_job_card(card)
                    if job_data:
                        self.jobs.append(job_data)
                
                logger.info(f"Page {page + 1}: Found {len(job_cards)} jobs, Total: {len(self.jobs)}")
                
                page += 1
                start += 10
                
                # Random delay to avoid rate limiting
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {str(e)}")
                break
        
        return self.jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse individual job card"""
        try:
            # Job title and link
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            job_title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
            job_id = title_link.get('data-jk', '') if title_link else ''
            job_url = f"{self.BASE_URL}/viewjob?jk={job_id}" if job_id else ""
            
            # Company name
            company_elem = card.find('span', {'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find('div', {'data-testid': 'text-location'})
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet')
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Job snippet/description
            snippet_elem = card.find('div', class_='job-snippet')
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Job attributes (full-time, remote, etc.)
            attributes = []
            attr_elems = card.find_all('div', class_='attribute_snippet')
            for attr in attr_elems:
                attributes.append(attr.get_text(strip=True))
            
            # Post date
            date_elem = card.find('span', class_='date')
            posted_date = date_elem.get_text(strip=True) if date_elem else ""
            
            job_data = {
                'id': job_id,
                'title': job_title,
                'company': company,
                'location': location,
                'salary': salary,
                'description_snippet': snippet,
                'url': job_url,
                'attributes': attributes,
                'posted_date': posted_date,
                'source': 'indeed',
                'scraped_at': datetime.now().isoformat()
            }
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing job card: {str(e)}")
            return None
    
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Fetch full job details"""
        url = f"{self.BASE_URL}/viewjob?jk={job_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Full job description
            desc_elem = soup.find('div', id='jobDescriptionText')
            description = desc_elem.get_text('\n', strip=True) if desc_elem else ""
            
            return {
                'full_description': description
            }
            
        except Exception as e:
            logger.error(f"Error fetching job details for {job_id}: {str(e)}")
            return None
    
    def save_jobs(self, filename: str = 'indeed_jobs.json'):
        """Save scraped jobs to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.jobs)} jobs to {filename}")


def main():
    """Example usage"""
    scraper = IndeedScraper()
    
    # Search for jobs
    jobs = scraper.search_jobs(
        job_title="Senior Software Engineer",
        location="London",
        max_results=50,
        job_type="fulltime"
    )
    
    # Enrich with full descriptions for top matches
    for i, job in enumerate(jobs[:10]):
        logger.info(f"Fetching details for job {i+1}/10")
        details = scraper.get_job_details(job['id'])
        if details:
            job.update(details)
        time.sleep(random.uniform(1, 3))
    
    # Save results
    scraper.save_jobs('indeed_jobs.json')
    
    print(f"\n✅ Scraped {len(jobs)} jobs from Indeed")


if __name__ == "__main__":
    main()
