#!/usr/bin/env python3
"""
Enhanced Campaign Executor for Multi-Platform Job Applications
Properly handles module imports and execution
"""

import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime
import traceback

# Add script paths
sys.path.insert(0, '.github/scripts')

def load_platform_modules():
    """Load and validate all platform modules"""
    platforms = {}
    
    # LinkedIn
    try:
        from linkedin_advanced_networking import AdvancedLinkedInNetworking
        platforms['linkedin'] = {
            'class': AdvancedLinkedInNetworking,
            'methods': ['add_connection_target', 'save_data']
        }
        print("✅ LinkedIn Advanced Networking loaded")
    except ImportError as e:
        try:
            from linkedin_automation import LinkedInAutomation
            platforms['linkedin'] = {
                'class': LinkedInAutomation,
                'methods': ['connect_with_person', 'save_connections']
            }
            print("✅ LinkedIn Automation loaded")
        except ImportError:
            print(f"⚠️ LinkedIn modules not available: {e}")
    
    # Indeed
    try:
        from indeed_scraper import IndeedScraper
        platforms['indeed'] = {
            'class': IndeedScraper,
            'methods': ['search_jobs', 'save_jobs']
        }
        print("✅ Indeed Scraper loaded")
    except ImportError as e:
        print(f"⚠️ Indeed module not available: {e}")
    
    # Reed
    try:
        from reed_scraper import ReedScraper
        platforms['reed'] = {
            'class': ReedScraper,
            'methods': ['search_jobs', 'save_jobs']
        }
        print("✅ Reed Scraper loaded")
    except ImportError as e:
        print(f"⚠️ Reed module not available: {e}")
    
    # Glassdoor
    try:
        from glassdoor_automation import GlassdoorAutomation
        platforms['glassdoor'] = {
            'class': GlassdoorAutomation,
            'methods': ['add_company_to_research', 'save_data']
        }
        print("✅ Glassdoor Automation loaded")
    except ImportError:
        try:
            from enhanced_glassdoor_automation import EnhancedGlassdoorAutomation
            platforms['glassdoor'] = {
                'class': EnhancedGlassdoorAutomation,
                'methods': ['research_company', 'save_research']
            }
            print("✅ Enhanced Glassdoor Automation loaded")
        except ImportError as e:
            print(f"⚠️ Glassdoor modules not available: {e}")
    
    return platforms


def process_linkedin(platform_class, contacts, dry_run):
    """Process LinkedIn connections"""
    results = {'applications': 0, 'successful': 0, 'failed': 0}
    
    try:
        linkedin = platform_class()
        print(f"   📊 Processing {len(contacts)} LinkedIn contacts...")
        
        for i, contact in enumerate(contacts[:10], 1):  # Limit to 10 for safety
            try:
                name = contact.get('name', 'Unknown')
                print(f"      [{i}/{min(10, len(contacts))}] {name}")
                
                # Try different method names based on what's available
                if hasattr(linkedin, 'add_connection_target'):
                    result = linkedin.add_connection_target(
                        profile_url=contact.get('profile_url', ''),
                        name=name,
                        company=contact.get('company', ''),
                        position=contact.get('position', ''),
                        industry=contact.get('industry', 'technology'),
                        priority='high'
                    )
                elif hasattr(linkedin, 'connect_with_person'):
                    result = linkedin.connect_with_person(
                        profile_url=contact.get('profile_url', ''),
                        name=name,
                        message=f"Hi {name}, I'd love to connect!"
                    )
                else:
                    print(f"         ⚠️ No suitable method found")
                    results['failed'] += 1
                    continue
                
                if result and result.get('success'):
                    results['successful'] += 1
                    print(f"         ✅ Success")
                else:
                    results['failed'] += 1
                    print(f"         ❌ Failed: {result.get('error', 'Unknown error')}")
                
                results['applications'] += 1
                
            except Exception as e:
                print(f"         ❌ Error: {e}")
                results['failed'] += 1
        
        # Save data
        if not dry_run:
            if hasattr(linkedin, 'save_data'):
                linkedin.save_data()
            elif hasattr(linkedin, 'save_connections'):
                linkedin.save_connections()
            print(f"   💾 Data saved")
        
    except Exception as e:
        print(f"   ❌ LinkedIn initialization error: {e}")
        traceback.print_exc()
    
    return results


def process_indeed(platform_class, target_jobs, locations, modes, companies, campaign_name, dry_run):
    """Process Indeed job searches"""
    results = {'applications': 0, 'successful': 0, 'failed': 0}
    
    try:
        indeed = platform_class()
        all_jobs = []
        
        for job_title in target_jobs:
            for location in locations:
                try:
                    print(f"      🔍 Searching: '{job_title}' in {location}")
                    
                    jobs = indeed.search_jobs(
                        job_title=job_title,
                        location=location,
                        max_results=10
                    )
                    
                    print(f"         Found {len(jobs)} jobs")
                    
                    # Filter by mode
                    if modes:
                        mode_keywords = [m.lower() for m in modes]
                        filtered = [
                            j for j in jobs
                            if any(kw in str(j.get('attributes', [])).lower() 
                                  or kw in str(j.get('description', '')).lower()
                                  for kw in mode_keywords)
                        ]
                        print(f"         {len(filtered)} after mode filter")
                        jobs = filtered
                    
                    # Filter by company
                    if companies:
                        filtered = [
                            j for j in jobs
                            if any(c.lower() in j.get('company', '').lower() 
                                  for c in companies)
                        ]
                        print(f"         {len(filtered)} after company filter")
                        jobs = filtered
                    
                    all_jobs.extend(jobs)
                    results['applications'] += len(jobs)
                    results['successful'] += len(jobs)
                    
                    print(f"         ✅ {len(jobs)} jobs queued")
                    
                except Exception as e:
                    print(f"         ❌ Search error: {e}")
                    results['failed'] += 1
        
        # Save jobs
        if not dry_run and all_jobs:
            output_file = f'job_search/indeed_jobs_{campaign_name}.json'
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(all_jobs, f, indent=2)
            
            print(f"   💾 {len(all_jobs)} jobs saved to {output_file}")
        
    except Exception as e:
        print(f"   ❌ Indeed error: {e}")
        traceback.print_exc()
    
    return results


def process_reed(platform_class, target_jobs, locations, modes, companies, campaign_name, dry_run):
    """Process Reed job searches"""
    results = {'applications': 0, 'successful': 0, 'failed': 0}
    
    try:
        reed = platform_class()
        all_jobs = []
        
        for job_title in target_jobs:
            for location in locations:
                try:
                    print(f"      🔍 Searching: '{job_title}' in {location}")
                    
                    # Check what methods are available
                    if hasattr(reed, 'search_jobs'):
                        jobs = reed.search_jobs(
                            keywords=job_title,
                            location=location,
                            max_results=10
                        )
                    else:
                        print(f"         ⚠️ search_jobs method not found")
                        continue
                    
                    print(f"         Found {len(jobs)} jobs")
                    
                    # Apply filters similar to Indeed
                    if modes:
                        mode_keywords = [m.lower() for m in modes]
                        jobs = [
                            j for j in jobs
                            if any(kw in str(j).lower() for kw in mode_keywords)
                        ]
                    
                    if companies:
                        jobs = [
                            j for j in jobs
                            if any(c.lower() in j.get('employerName', '').lower() 
                                  for c in companies)
                        ]
                    
                    all_jobs.extend(jobs)
                    results['applications'] += len(jobs)
                    results['successful'] += len(jobs)
                    
                    print(f"         ✅ {len(jobs)} jobs queued")
                    
                except Exception as e:
                    print(f"         ❌ Search error: {e}")
                    results['failed'] += 1
        
        # Save jobs
        if not dry_run and all_jobs:
            output_file = f'job_search/reed_jobs_{campaign_name}.json'
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(all_jobs, f, indent=2)
            
            print(f"   💾 {len(all_jobs)} jobs saved")
        
    except Exception as e:
        print(f"   ❌ Reed error: {e}")
        traceback.print_exc()
    
    return results


def process_glassdoor(platform_class, companies, dry_run):
    """Process Glassdoor company research"""
    results = {'applications': 0, 'successful': 0, 'failed': 0}
    
    try:
        glassdoor = platform_class()
        
        for company in companies:
            try:
                print(f"      🏢 Researching: {company}")
                
                if hasattr(glassdoor, 'add_company_to_research'):
                    result = glassdoor.add_company_to_research(
                        company_name=company,
                        priority='high',
                        reason='job_application'
                    )
                elif hasattr(glassdoor, 'research_company'):
                    result = glassdoor.research_company(company_name=company)
                else:
                    print(f"         ⚠️ No suitable method found")
                    results['failed'] += 1
                    continue
                
                if result and result.get('success'):
                    results['successful'] += 1
                    results['applications'] += 1
                    print(f"         ✅ Queued for research")
                else:
                    results['failed'] += 1
                    print(f"         ❌ Failed")
                
            except Exception as e:
                print(f"         ❌ Error: {e}")
                results['failed'] += 1
        
        # Save data
        if not dry_run:
            if hasattr(glassdoor, 'save_data'):
                glassdoor.save_data()
            elif hasattr(glassdoor, 'save_research'):
                glassdoor.save_research()
            print(f"   💾 Data saved")
        
    except Exception as e:
        print(f"   ❌ Glassdoor error: {e}")
        traceback.print_exc()
    
    return results


def main():
    print("=" * 70)
    print("🚀 EXECUTING MULTI-PLATFORM JOB APPLICATIONS")
    print("=" * 70)
    
    # Load execution plan
    with open('campaign_execution_plan.json', 'r') as f:
        plan = json.load(f)
    
    campaigns = plan['campaigns_to_run']
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    print(f"\nMode: {'🧪 DRY RUN' if dry_run else '✅ LIVE'}")
    print(f"Campaigns to execute: {len(campaigns)}\n")
    
    # Load platform modules
    platforms_available = load_platform_modules()
    
    if not platforms_available:
        print("\n❌ No platform modules available!")
        print("   Check that .github/scripts/ contains the required modules")
        sys.exit(1)
    
    # Execution tracking
    execution_results = {
        'start_time': datetime.now().isoformat(),
        'campaigns': [],
        'total_applications': 0,
        'successful': 0,
        'failed': 0,
        'platforms': {}
    }
    
    # Process each campaign
    for campaign_info in campaigns:
        campaign_name = campaign_info['name']
        config = campaign_info['config']
        
        print(f"\n{'=' * 70}")
        print(f"📋 CAMPAIGN: {campaign_name}")
        print(f"{'=' * 70}")
        
        campaign_result = {
            'name': campaign_name,
            'platforms': [],
            'applications': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Load contacts
        contacts_dir = config.get('target_contacts_dir', 'contacts')
        contacts_file = config.get('target_contacts_file', 'contacts.csv')
        contacts_path = Path(contacts_dir) / contacts_file
        
        contacts = []
        if contacts_path.exists():
            try:
                with open(contacts_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    contacts = list(reader)
                print(f"✅ Loaded {len(contacts)} contacts")
            except Exception as e:
                print(f"⚠️ Error loading contacts: {e}")
        
        # Get campaign parameters
        platforms = config.get('platform', [])
        target_jobs = config.get('target_jobs', [])
        locations = config.get('Location', [])
        modes = config.get('Mode', [])
        companies = config.get('company', [])
        
        print(f"\n📊 Parameters:")
        print(f"   Jobs: {', '.join(target_jobs)}")
        print(f"   Locations: {', '.join(locations)}")
        print(f"   Modes: {', '.join(modes)}")
        print(f"   Platforms: {', '.join(platforms)}")
        if companies:
            print(f"   Companies: {', '.join(companies)}")
        
        # Process each platform
        for platform_name in platforms:
            platform_lower = platform_name.lower()
            print(f"\n🎯 Platform: {platform_name}")
            
            platform_result = {
                'platform': platform_name,
                'applications': 0,
                'successful': 0,
                'failed': 0
            }
            
            try:
                if platform_lower == 'linkedin' and 'linkedin' in platforms_available:
                    result = process_linkedin(
                        platforms_available['linkedin']['class'],
                        contacts,
                        dry_run
                    )
                    platform_result.update(result)
                
                elif platform_lower == 'indeed' and 'indeed' in platforms_available:
                    result = process_indeed(
                        platforms_available['indeed']['class'],
                        target_jobs, locations, modes, companies,
                        campaign_name, dry_run
                    )
                    platform_result.update(result)
                
                elif platform_lower == 'reed' and 'reed' in platforms_available:
                    result = process_reed(
                        platforms_available['reed']['class'],
                        target_jobs, locations, modes, companies,
                        campaign_name, dry_run
                    )
                    platform_result.update(result)
                
                elif platform_lower == 'glassdoor' and 'glassdoor' in platforms_available:
                    result = process_glassdoor(
                        platforms_available['glassdoor']['class'],
                        companies if companies else ['Example Corp'],
                        dry_run
                    )
                    platform_result.update(result)
                
                else:
                    print(f"   ⚠️ Platform not available or not supported")
                
            except Exception as e:
                print(f"   ❌ Platform error: {e}")
                traceback.print_exc()
                campaign_result['errors'].append(f"{platform_name}: {str(e)}")
            
            campaign_result['platforms'].append(platform_result)
            campaign_result['applications'] += platform_result['applications']
            campaign_result['successful'] += platform_result['successful']
            campaign_result['failed'] += platform_result['failed']
            
            print(f"   📊 Results: {platform_result['successful']}/{platform_result['applications']} successful")
        
        execution_results['campaigns'].append(campaign_result)
        execution_results['total_applications'] += campaign_result['applications']
        execution_results['successful'] += campaign_result['successful']
        execution_results['failed'] += campaign_result['failed']
        
        print(f"\n✅ Campaign complete:")
        print(f"   Total: {campaign_result['applications']}")
        print(f"   Successful: {campaign_result['successful']}")
        print(f"   Failed: {campaign_result['failed']}")
    
    execution_results['end_time'] = datetime.now().isoformat()
    execution_results['dry_run'] = dry_run
    
    # Save results
    with open('campaign_execution_results.json', 'w') as f:
        json.dump(execution_results, f, indent=2)
    
    # Save to tracking
    tracking_dir = Path('job_search')
    tracking_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(tracking_dir / f'campaign_execution_{timestamp}.json', 'w') as f:
        json.dump(execution_results, f, indent=2)
    
    print(f"\n{'=' * 70}")
    print(f"📊 EXECUTION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total: {execution_results['total_applications']}")
    print(f"Successful: {execution_results['successful']}")
    print(f"Failed: {execution_results['failed']}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    # Set GitHub outputs
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"total_applications={execution_results['total_applications']}\n")
            f.write(f"successful={execution_results['successful']}\n")
            f.write(f"failed={execution_results['failed']}\n")
    
    print(f"\n✅ Execution complete!")


if __name__ == '__main__':
    main()
