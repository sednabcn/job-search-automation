#!/usr/bin/env python3
"""
Multi-Platform Job Search CLI
Unified command-line interface for LinkedIn, Glassdoor, Indeed, and Reed
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiPlatformJobSearch:
    """Unified job search across multiple platforms"""
    
    SUPPORTED_PLATFORMS = ['linkedin', 'glassdoor', 'indeed', 'reed']
    
    def __init__(self, config_file: str = 'job-manager-config.yml'):
        self.config_file = config_file
        self.config = self._load_config()
        self.results = {}
    
    def _load_config(self) -> Dict:
        """Load configuration file"""
        try:
            import yaml
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {}
    
    def search_all_platforms(self, 
                            job_positions: List[str],
                            location: str = "London",
                            max_per_platform: int = 50) -> Dict:
        """Search across all enabled platforms"""
        logger.info(f"Starting multi-platform search for: {', '.join(job_positions)}")
        
        platforms = self.config.get('platforms', {})
        
        for platform in self.SUPPORTED_PLATFORMS:
            if platform not in platforms:
                continue
            
            platform_config = platforms[platform]
            max_results = platform_config.get('max_results_per_search', max_per_platform)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Searching {platform.upper()}")
            logger.info(f"{'='*60}")
            
            try:
                jobs = self._search_platform(platform, job_positions, location, max_results)
                self.results[platform] = jobs
                logger.info(f"✅ Found {len(jobs)} jobs on {platform}")
            except Exception as e:
                logger.error(f"❌ {platform} search failed: {str(e)}")
                self.results[platform] = []
        
        return self.results
    
    def _search_platform(self, 
                        platform: str, 
                        job_positions: List[str],
                        location: str,
                        max_results: int) -> List[Dict]:
        """Search a specific platform"""
        
        if platform == 'linkedin':
            return self._search_linkedin(job_positions, location, max_results)
        elif platform == 'glassdoor':
            return self._search_glassdoor(job_positions, location, max_results)
        elif platform == 'indeed':
            return self._search_indeed(job_positions, location, max_results)
        elif platform == 'reed':
            return self._search_reed(job_positions, location, max_results)
        else:
            logger.warning(f"Unknown platform: {platform}")
            return []
    
    def _search_linkedin(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search LinkedIn"""
        try:
            from linkedin_automotion import LinkedInAutomation
            
            linkedin = LinkedInAutomation()
            all_jobs = []
            
            for position in positions:
                jobs = linkedin.search_jobs(position, location, max_results // len(positions))
                all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("LinkedIn scraper not found")
            return []
    
    def _search_glassdoor(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search Glassdoor"""
        try:
            from enhanced_glassdoor_automotion import GlassdoorScraper
            
            glassdoor = GlassdoorScraper()
            all_jobs = []
            
            for position in positions:
                jobs = glassdoor.search_jobs(position, location, max_results // len(positions))
                all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("Glassdoor scraper not found")
            return []
    
    def _search_indeed(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search Indeed"""
        try:
            from indeed_scraper import IndeedScraper
            
            indeed = IndeedScraper()
            all_jobs = []
            
            for position in positions:
                jobs = indeed.search_jobs(position, location, max_results // len(positions))
                all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("Indeed scraper not found")
            return []
    
    def _search_reed(self, positions: List[str], location: str, max_results: int) -> List[Dict]:
        """Search Reed"""
        try:
            from reed_scraper import ReedScraper
            import os
            
            # Try API first if key is available
            api_key = os.getenv('REED_API_KEY')
            reed = ReedScraper(api_key=api_key)
            
            all_jobs = []
            
            if api_key:
                logger.info("Using Reed API")
                for position in positions:
                    jobs = reed.search_with_api(position, location, max_results // len(positions))
                    all_jobs.extend(jobs)
            else:
                logger.info("Using Reed web scraping")
                for position in positions:
                    jobs = reed.search_jobs(position, location, max_results // len(positions))
                    all_jobs.extend(jobs)
            
            return all_jobs
        except ImportError:
            logger.error("Reed scraper not found")
            return []
    
    def merge_results(self) -> List[Dict]:
        """Merge and deduplicate results from all platforms"""
        all_jobs = []
        seen_ids = set()
        
        for platform, jobs in self.results.items():
            for job in jobs:
                # Create unique identifier
                job_id = (job.get('id') or 
                         f"{job.get('company', 'unknown')}_{job.get('title', 'unknown')}")
                
                if job_id not in seen_ids:
                    job['platforms'] = [platform]
                    all_jobs.append(job)
                    seen_ids.add(job_id)
                else:
                    # Job found on multiple platforms
                    for existing_job in all_jobs:
                        existing_id = (existing_job.get('id') or 
                                      f"{existing_job.get('company', 'unknown')}_{existing_job.get('title', 'unknown')}")
                        if existing_id == job_id:
                            existing_job['platforms'].append(platform)
                            break
        
        logger.info(f"\n✅ Total unique jobs found: {len(all_jobs)}")
        
        # Find jobs on multiple platforms
        multi_platform = [j for j in all_jobs if len(j.get('platforms', [])) > 1]
        if multi_platform:
            logger.info(f"   Jobs found on multiple platforms: {len(multi_platform)}")
        
        return all_jobs
    
    def save_results(self, output_file: str = 'all_jobs_combined.json'):
        """Save merged results"""
        merged = self.merge_results()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {len(merged)} jobs to {output_file}")
        
        # Also save platform-specific files
        for platform, jobs in self.results.items():
            platform_file = f"{platform}_jobs.json"
            with open(platform_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"   Saved {len(jobs)} {platform} jobs to {platform_file}")
    
    def print_summary(self):
        """Print search summary"""
        print("\n" + "="*60)
        print("📊 MULTI-PLATFORM SEARCH SUMMARY")
        print("="*60)
        
        for platform, jobs in sorted(self.results.items()):
            print(f"\n{platform.upper()}:")
            print(f"  Total jobs: {len(jobs)}")
            
            if jobs:
                companies = len(set(j.get('company', '') for j in jobs))
                locations = len(set(j.get('location', '') for j in jobs))
                with_salary = sum(1 for j in jobs if j.get('salary'))
                
                print(f"  Unique companies: {companies}")
                print(f"  Locations: {locations}")
                print(f"  With salary info: {with_salary} ({with_salary/len(jobs)*100:.1f}%)")
        
        merged = self.merge_results()
        print(f"\n{'='*60}")
        print(f"TOTAL UNIQUE JOBS: {len(merged)}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Multi-Platform Job Search CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search all platforms for specific roles
  %(prog)s search --positions "Senior Software Engineer" "Tech Lead" --location London

  # Search specific platforms only
  %(prog)s search --platforms indeed reed --positions "Python Developer"

  # Extract keywords from existing job files
  %(prog)s extract-keywords --files "*_jobs.json"

  # Update configuration with extracted keywords
  %(prog)s extract-keywords --update-config

  # Show platform statistics
  %(prog)s stats

Supported Platforms:
  - LinkedIn
  - Glassdoor  
  - Indeed
  - Reed
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for jobs')
    search_parser.add_argument(
        '--positions',
        nargs='+',
        required=True,
        help='Job positions to search for'
    )
    search_parser.add_argument(
        '--location',
        default='London',
        help='Location to search (default: London)'
    )
    search_parser.add_argument(
        '--platforms',
        nargs='+',
        choices=['linkedin', 'glassdoor', 'indeed', 'reed', 'all'],
        default=['all'],
        help='Platforms to search (default: all)'
    )
    search_parser.add_argument(
        '--max-per-platform',
        type=int,
        default=50,
        help='Maximum results per platform (default: 50)'
    )
    search_parser.add_argument(
        '--output',
        default='all_jobs_combined.json',
        help='Output file for combined results'
    )
    search_parser.add_argument(
        '--config',
        default='job-manager-config.yml',
        help='Configuration file to use'
    )
    
    # Extract keywords command
    extract_parser = subparsers.add_parser('extract-keywords', help='Extract keywords from jobs')
    extract_parser.add_argument(
        '--files',
        nargs='+',
        default=['*_jobs.json'],
        help='Job files to analyze (supports wildcards)'
    )
    extract_parser.add_argument(
        '--positions',
        nargs='+',
        help='Job positions (if not in config)'
    )
    extract_parser.add_argument(
        '--update-config',
        action='store_true',
        help='Update job-manager-config.yml with extracted keywords'
    )
    extract_parser.add_argument(
        '--output',
        default='keyword_analysis_report.json',
        help='Output file for analysis report'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument(
        '--files',
        nargs='+',
        default=['*_jobs.json'],
        help='Job files to analyze'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'search':
        searcher = MultiPlatformJobSearch(config_file=args.config)
        
        # Determine platforms
        if 'all' in args.platforms:
            platforms_to_search = searcher.SUPPORTED_PLATFORMS
        else:
            platforms_to_search = args.platforms
        
        # Override config with selected platforms
        if not searcher.config.get('platforms'):
            searcher.config['platforms'] = {}
        
        for platform in platforms_to_search:
            if platform not in searcher.config['platforms']:
                searcher.config['platforms'][platform] = {
                    'max_results_per_search': args.max_per_platform
                }
        
        # Perform search
        searcher.search_all_platforms(
            args.positions,
            args.location,
            args.max_per_platform
        )
        
        # Save and display results
        searcher.save_results(args.output)
        searcher.print_summary()
    
    elif args.command == 'extract-keywords':
        from keyword_extractor import KeywordExtractor
        
        # Get positions from args or config
        if args.positions:
            positions = args.positions
        else:
            try:
                import yaml
                with open('job-manager-config.yml', 'r') as f:
                    config = yaml.safe_load(f)
                positions = config.get('search', {}).get('target_roles', [])
            except:
                positions = ['Senior Software Engineer', 'Staff Engineer']
        
        # Initialize extractor
        extractor = KeywordExtractor(positions)
        
        # Load and analyze jobs
        jobs = extractor.load_jobs_from_files(args.files)
        if not jobs:
            logger.error("No job files found!")
            sys.exit(1)
        
        extractor.extract_keywords(jobs)
        
        # Generate reports
        extractor.export_analysis_report(args.output)
        
        if args.update_config:
            extractor.generate_config('job-manager-config.yml')
            logger.info("✅ Configuration updated")
        else:
            extractor.generate_config('job-manager-config-preview.yml')
            logger.info("✅ Preview saved to job-manager-config-preview.yml")
    
    elif args.command == 'stats':
        from pathlib import Path
        from collections import defaultdict
        
        stats = defaultdict(dict)
        total_jobs = 0
        
        for pattern in args.files:
            for job_file in Path('.').glob(pattern):
                try:
                    platform = job_file.stem.replace('_jobs', '')
                    with open(job_file, 'r') as f:
                        jobs = json.load(f)
                    
                    stats[platform]['total'] = len(jobs)
                    stats[platform]['companies'] = len(set(j.get('company', '') for j in jobs))
                    stats[platform]['with_salary'] = sum(1 for j in jobs if j.get('salary'))
                    
                    total_jobs += len(jobs)
                except Exception as e:
                    logger.error(f"Error reading {job_file}: {e}")
        
        print("\n" + "="*60)
        print("📊 JOB SEARCH STATISTICS")
        print("="*60)
        
        for platform, data in sorted(stats.items()):
            print(f"\n{platform.upper()}:")
            for key, value in data.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n{'='*60}")
        print(f"TOTAL JOBS: {total_jobs}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
