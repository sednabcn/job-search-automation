#!/usr/bin/env python3
"""
Campaign Validator & Creator Tool
Validates campaign JSON files and helps create new campaigns interactively
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class CampaignValidator:
    """Validate and create multi-platform job application campaigns"""
    
    REQUIRED_FIELDS = [
        'cv_dir', 'cv_file', 'target_jobs', 'platform', 'Location', 'send'
    ]
    
    OPTIONAL_FIELDS = [
        'cover_letter_dir', 'cover_letter_file', 'letter_dir', 'letter_file',
        'target_contacts_dir', 'target_contacts_file', 'Mode', 'company',
        'timestamp', 'notification_to_user'
    ]
    
    VALID_PLATFORMS = ['linkedin', 'indeed', 'reed', 'glassdoor']
    
    VALID_SEND_MODES = [
        'immediate', 'now', 'tomorrow', 'each_day', 'daily', 
        'each_week', 'weekly', 'cron', 'delay', 'timestamp'
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_campaign(self, campaign: Dict, campaign_name: str = "campaign") -> bool:
        """Validate a campaign configuration"""
        
        print(f"\n{'='*60}")
        print(f"🔍 Validating: {campaign_name}")
        print(f"{'='*60}")
        
        self.errors = []
        self.warnings = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in campaign:
                self.errors.append(f"Missing required field: {field}")
            elif not campaign[field]:
                self.errors.append(f"Empty required field: {field}")
        
        # Validate platforms
        if 'platform' in campaign:
            platforms = campaign['platform']
            if not isinstance(platforms, list):
                self.errors.append("'platform' must be a list")
            else:
                for platform in platforms:
                    if platform.lower() not in self.VALID_PLATFORMS:
                        self.warnings.append(
                            f"Unknown platform '{platform}'. Valid: {', '.join(self.VALID_PLATFORMS)}"
                        )
        
        # Validate send mode
        if 'send' in campaign:
            send_mode = campaign['send'].lower()
            if not any(send_mode.startswith(mode) for mode in self.VALID_SEND_MODES):
                self.warnings.append(
                    f"Unknown send mode '{send_mode}'. Valid: {', '.join(self.VALID_SEND_MODES)}"
                )
            
            # Check timestamp format if needed
            if send_mode in ['tomorrow', 'timestamp'] and 'timestamp' in campaign:
                timestamp = campaign['timestamp']
                if timestamp:
                    try:
                        datetime.strptime(timestamp, '%m/%d/%Y:%H:%M:%S')
                    except ValueError:
                        self.errors.append(
                            f"Invalid timestamp format: {timestamp}. Expected: MM/DD/YYYY:HH:MM:SS"
                        )
        
        # Validate target_jobs
        if 'target_jobs' in campaign:
            if not isinstance(campaign['target_jobs'], list):
                self.errors.append("'target_jobs' must be a list")
            elif len(campaign['target_jobs']) == 0:
                self.warnings.append("'target_jobs' list is empty")
        
        # Validate locations
        if 'Location' in campaign:
            if not isinstance(campaign['Location'], list):
                self.errors.append("'Location' must be a list")
            elif len(campaign['Location']) == 0:
                self.warnings.append("'Location' list is empty - will not filter by location")
        
        # Check file paths exist
        file_checks = [
            ('cv_dir', 'cv_file'),
            ('cover_letter_dir', 'cover_letter_file'),
            ('letter_dir', 'letter_file'),
            ('target_contacts_dir', 'target_contacts_file')
        ]
        
        for dir_field, file_field in file_checks:
            if dir_field in campaign and file_field in campaign:
                if campaign[dir_field] and campaign[file_field]:
                    file_path = Path(campaign[dir_field]) / campaign[file_field]
                    if not file_path.exists():
                        self.warnings.append(f"File not found: {file_path}")
        
        # Print results
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ Campaign configuration is valid!")
        elif not self.errors:
            print("\n✅ Campaign is valid (with warnings)")
        else:
            print("\n❌ Campaign has errors and cannot be executed")
        
        return len(self.errors) == 0
    
    def create_campaign_interactive(self) -> Dict:
        """Create a campaign configuration interactively"""
        
        print("\n" + "="*60)
        print("📝 INTERACTIVE CAMPAIGN CREATOR")
        print("="*60)
        
        campaign = {}
        
        # Basic info
        print("\n1️⃣  Basic Information")
        campaign['cv_dir'] = input("CV directory [cv]: ").strip() or "cv"
        campaign['cv_file'] = input("CV filename [my_cv.txt]: ").strip() or "my_cv.txt"
        
        campaign['cover_letter_dir'] = input("Cover letter directory [cover_letter]: ").strip() or "cover_letter"
        campaign['cover_letter_file'] = input("Cover letter filename [cover_letter.txt]: ").strip() or "cover_letter.txt"
        
        # Target jobs
        print("\n2️⃣  Target Jobs (comma-separated)")
        jobs_input = input("Job titles: ").strip()
        campaign['target_jobs'] = [j.strip() for j in jobs_input.split(',') if j.strip()]
        
        # Platforms
        print("\n3️⃣  Platforms")
        print(f"   Available: {', '.join(self.VALID_PLATFORMS)}")
        platforms_input = input("Platforms (comma-separated) [linkedin,indeed]: ").strip()
        if platforms_input:
            campaign['platform'] = [p.strip().lower() for p in platforms_input.split(',')]
        else:
            campaign['platform'] = ['linkedin', 'indeed']
        
        # Locations
        print("\n4️⃣  Locations (comma-separated)")
        locations_input = input("Locations [London]: ").strip()
        if locations_input:
            campaign['Location'] = [l.strip() for l in locations_input.split(',')]
        else:
            campaign['Location'] = ['London']
        
        # Mode
        print("\n5️⃣  Work Mode (comma-separated)")
        print("   Options: Remote, Hybrid, On-site")
        mode_input = input("Work modes [Remote,Hybrid]: ").strip()
        if mode_input:
            campaign['Mode'] = [m.strip() for m in mode_input.split(',')]
        else:
            campaign['Mode'] = ['Remote', 'Hybrid']
        
        # Target companies (optional)
        print("\n6️⃣  Target Companies (optional, comma-separated)")
        companies_input = input("Companies (or press Enter to skip): ").strip()
        if companies_input:
            campaign['company'] = [c.strip() for c in companies_input.split(',')]
        else:
            campaign['company'] = []
        
        # Contacts
        print("\n7️⃣  Contacts")
        campaign['target_contacts_dir'] = input("Contacts directory [contacts]: ").strip() or "contacts"
        campaign['target_contacts_file'] = input("Contacts filename [contacts.csv]: ").strip() or "contacts.csv"
        
        # Schedule
        print("\n8️⃣  Schedule")
        print("   Options:")
        print("   1. immediate - Run right away")
        print("   2. tomorrow - Run tomorrow")
        print("   3. each_day - Run daily")
        print("   4. each_week - Run weekly (Mondays)")
        print("   5. timestamp - Specific date/time")
        
        schedule_choice = input("Choose schedule [1]: ").strip() or "1"
        
        schedule_map = {
            '1': 'immediate',
            '2': 'tomorrow',
            '3': 'each_day',
            '4': 'each_week',
            '5': 'timestamp'
        }
        
        campaign['send'] = schedule_map.get(schedule_choice, 'immediate')
        
        if campaign['send'] in ['tomorrow', 'timestamp']:
            timestamp = input("Timestamp (MM/DD/YYYY:HH:MM:SS): ").strip()
            campaign['timestamp'] = timestamp
        else:
            campaign['timestamp'] = ""
        
        # Notification
        print("\n9️⃣  Notifications")
        email = input("Notification email (optional): ").strip()
        campaign['notification_to_user'] = email
        
        # Additional fields for compatibility
        campaign['letter_dir'] = campaign['cover_letter_dir']
        campaign['letter_file'] = campaign['cover_letter_file']
        
        return campaign
    
    def save_campaign(self, campaign: Dict, filename: str, 
                     campaigns_dir: str = "scheduled-campaigns") -> bool:
        """Save campaign to JSON file"""
        
        campaigns_path = Path(campaigns_dir)
        campaigns_path.mkdir(exist_ok=True)
        
        filepath = campaigns_path / filename
        
        if not filename.endswith('.json'):
            filepath = campaigns_path / f"{filename}.json"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(campaign, f, indent=2)
            
            print(f"\n✅ Campaign saved to: {filepath}")
            return True
        
        except Exception as e:
            print(f"\n❌ Error saving campaign: {e}")
            return False
    
    def list_campaigns(self, campaigns_dir: str = "scheduled-campaigns"):
        """List all campaigns in directory"""
        
        campaigns_path = Path(campaigns_dir)
        
        if not campaigns_path.exists():
            print(f"❌ Campaigns directory not found: {campaigns_dir}")
            return []
        
        campaign_files = list(campaigns_path.glob("*.json"))
        
        if not campaign_files:
            print(f"📂 No campaigns found in {campaigns_dir}")
            return []
        
        print(f"\n{'='*60}")
        print(f"📋 CAMPAIGNS IN {campaigns_dir}")
        print(f"{'='*60}\n")
        
        campaigns = []
        
        for i, filepath in enumerate(sorted(campaign_files), 1):
            try:
                with open(filepath, 'r') as f:
                    campaign = json.load(f)
                
                name = filepath.stem
                send_mode = campaign.get('send', 'unknown')
                platforms = ', '.join(campaign.get('platform', []))
                jobs_count = len(campaign.get('target_jobs', []))
                
                print(f"{i}. {name}")
                print(f"   Send: {send_mode}")
                print(f"   Platforms: {platforms}")
                print(f"   Target jobs: {jobs_count}")
                print()
                
                campaigns.append({
                    'file': filepath,
                    'name': name,
                    'config': campaign
                })
            
            except Exception as e:
                print(f"{i}. {filepath.name}")
                print(f"   ❌ Error loading: {e}")
                print()
        
        return campaigns
    
    def validate_directory(self, campaigns_dir: str = "scheduled-campaigns") -> bool:
        """Validate all campaigns in directory"""
        
        campaigns = self.list_campaigns(campaigns_dir)
        
        if not campaigns:
            return False
        
        print(f"\n{'='*60}")
        print("🔍 VALIDATING ALL CAMPAIGNS")
        print(f"{'='*60}")
        
        all_valid = True
        
        for campaign_info in campaigns:
            is_valid = self.validate_campaign(
                campaign_info['config'],
                campaign_info['name']
            )
            
            if not is_valid:
                all_valid = False
        
        print(f"\n{'='*60}")
        if all_valid:
            print("✅ All campaigns are valid!")
        else:
            print("❌ Some campaigns have errors")
        print(f"{'='*60}\n")
        
        return all_valid


def print_menu():
    """Print interactive menu"""
    print("\n" + "="*60)
    print("📋 CAMPAIGN MANAGER MENU")
    print("="*60)
    print("1. Create new campaign")
    print("2. Validate campaign file")
    print("3. List all campaigns")
    print("4. Validate all campaigns")
    print("5. Create example campaign")
    print("6. Help / Documentation")
    print("0. Exit")
    print("="*60)


def create_example_campaign():
    """Create a pre-configured example campaign"""
    
    example = {
        "cv_dir": "cv",
        "cv_file": "my_cv.txt",
        "cover_letter_dir": "cover_letter",
        "cover_letter_file": "my_cover.txt",
        "letter_dir": "letter",
        "letter_file": "my_letter.txt",
        "target_jobs": [
            "Software Engineer",
            "Senior Software Engineer",
            "Full Stack Developer"
        ],
        "target_contacts_dir": "contacts",
        "target_contacts_file": "contacts.csv",
        "platform": ["linkedin", "indeed", "reed"],
        "Location": ["London", "Greater London", "Remote"],
        "Mode": ["Remote", "Hybrid"],
        "company": [],
        "timestamp": "",
        "send": "immediate",
        "notification_to_user": "alerts@example.com"
    }
    
    return example


def print_help():
    """Print help documentation"""
    
    help_text = """
╔══════════════════════════════════════════════════════════════════╗
║                 CAMPAIGN CONFIGURATION GUIDE                     ║
╚══════════════════════════════════════════════════════════════════╝

REQUIRED FIELDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• cv_dir: Directory containing CV (e.g., "cv")
• cv_file: CV filename (e.g., "my_cv.txt")
• target_jobs: List of job titles to search for
  Example: ["Software Engineer", "Data Scientist"]
• platform: List of platforms to use
  Options: ["linkedin", "indeed", "reed", "glassdoor"]
• Location: List of locations to search in
  Example: ["London", "Greater London", "Remote"]
• send: Execution schedule mode (see below)

OPTIONAL FIELDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• cover_letter_dir/cover_letter_file: Cover letter details
• letter_dir/letter_file: Motivation letter details
• target_contacts_dir/target_contacts_file: Contacts CSV
• Mode: Work mode filter ["Remote", "Hybrid", "On-site"]
• company: Target specific companies (empty = all companies)
• timestamp: Specific execution time (MM/DD/YYYY:HH:MM:SS)
• notification_to_user: Email for notifications

SEND MODES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• immediate / now: Execute immediately when workflow runs
• tomorrow: Execute tomorrow at specified timestamp
• each_day / daily: Execute every day automatically
• each_week / weekly: Execute every Monday
• timestamp: Execute at specific date/time
• cron: Custom cron schedule (advanced)
• delay: Delay execution by specified time

CONTACTS CSV FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Headers: name,email,company,position,profile_url,industry,location

Example:
John Smith,john@company.com,Tech Corp,Engineer,https://linkedin.com/in/john,tech,London

PLATFORM-SPECIFIC NOTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LinkedIn:
  • Uses contacts CSV for networking
  • Requires profile_url field
  • Respects daily connection limits (5/day)

Indeed:
  • Searches jobs based on target_jobs and Location
  • Filters by Mode (Remote/Hybrid)
  • Can filter by specific companies

Reed:
  • Similar to Indeed
  • UK-focused job board

Glassdoor:
  • Company research and salary insights
  • Interview preparation
  • Requires company names

EXAMPLE CAMPAIGNS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Daily Tech Jobs:
   {
     "send": "each_day",
     "target_jobs": ["Software Engineer", "DevOps Engineer"],
     "platform": ["linkedin", "indeed"],
     "Location": ["London", "Remote"]
   }

2. Weekly Networking:
   {
     "send": "each_week",
     "target_jobs": ["Senior Engineer"],
     "platform": ["linkedin"],
     "Location": ["London"]
   }

3. Targeted Application:
   {
     "send": "immediate",
     "target_jobs": ["Data Scientist"],
     "platform": ["linkedin", "indeed", "glassdoor"],
     "company": ["Google", "Meta", "Amazon"],
     "Location": ["London"]
   }

WORKFLOW TRIGGERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Automatic: Runs every 6 hours checking for scheduled campaigns

Manual:
  gh workflow run job-application-multi-platform.yml
  gh workflow run job-application-multi-platform.yml --field dry_run=true
  gh workflow run job-application-multi-platform.yml --field campaign_file=my_campaign.json

BEST PRACTICES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Test with dry_run=true first
✓ Use daily campaigns for ongoing job search
✓ Use immediate for urgent applications
✓ Keep target_jobs focused (3-5 titles)
✓ Validate campaigns before committing
✓ Archive completed immediate campaigns
✓ Monitor GitHub issues for execution summaries
✓ Keep contacts CSV up to date

TROUBLESHOOTING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue: Campaign not running
  → Check send mode and timestamp
  → Verify campaign file is in scheduled-campaigns/
  → Check workflow logs in GitHub Actions

Issue: No jobs found
  → Verify target_jobs are realistic
  → Check Location spelling
  → Review Mode filters (some jobs may not specify)

Issue: Platform errors
  → Ensure required modules exist in .github/scripts/
  → Check module imports in workflow logs
  → Verify contacts CSV format for LinkedIn

For more help, check the GitHub repository README or create an issue.
"""
    
    print(help_text)


def main():
    """Main interactive interface"""
    
    validator = CampaignValidator()
    
    print("\n" + "="*60)
    print("🚀 MULTI-PLATFORM JOB APPLICATION CAMPAIGN MANAGER")
    print("="*60)
    print("\nManage job application campaigns across LinkedIn, Indeed, Reed, and Glassdoor")
    
    while True:
        print_menu()
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        
        elif choice == "1":
            # Create new campaign
            campaign = validator.create_campaign_interactive()
            
            print("\n" + "="*60)
            print("📄 CAMPAIGN PREVIEW")
            print("="*60)
            print(json.dumps(campaign, indent=2))
            
            if input("\nSave this campaign? (y/n): ").lower() == 'y':
                filename = input("Filename (without .json): ").strip()
                if validator.validate_campaign(campaign, filename):
                    validator.save_campaign(campaign, filename)
        
        elif choice == "2":
            # Validate specific file
            filename = input("Campaign filename: ").strip()
            filepath = Path("scheduled-campaigns") / filename
            
            if not filepath.exists():
                filepath = Path("scheduled-campaigns") / f"{filename}.json"
            
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        campaign = json.load(f)
                    validator.validate_campaign(campaign, filepath.stem)
                except Exception as e:
                    print(f"❌ Error loading file: {e}")
            else:
                print(f"❌ File not found: {filepath}")
        
        elif choice == "3":
            # List campaigns
            validator.list_campaigns()
        
        elif choice == "4":
            # Validate all
            validator.validate_directory()
        
        elif choice == "5":
            # Create example
            example = create_example_campaign()
            
            print("\n" + "="*60)
            print("📄 EXAMPLE CAMPAIGN")
            print("="*60)
            print(json.dumps(example, indent=2))
            
            if input("\nSave example campaign? (y/n): ").lower() == 'y':
                filename = input("Filename [example_campaign]: ").strip() or "example_campaign"
                validator.save_campaign(example, filename)
        
        elif choice == "6":
            # Help
            print_help()
        
        else:
            print("❌ Invalid option")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    import sys
    
    # Command line mode
    if len(sys.argv) > 1:
        validator = CampaignValidator()
        
        if sys.argv[1] == "validate":
            if len(sys.argv) > 2:
                # Validate specific file
                filepath = Path(sys.argv[2])
                if filepath.exists():
                    with open(filepath, 'r') as f:
                        campaign = json.load(f)
                    is_valid = validator.validate_campaign(campaign, filepath.stem)
                    sys.exit(0 if is_valid else 1)
                else:
                    print(f"❌ File not found: {filepath}")
                    sys.exit(1)
            else:
                # Validate all
                is_valid = validator.validate_directory()
                sys.exit(0 if is_valid else 1)
        
        elif sys.argv[1] == "list":
            validator.list_campaigns()
            sys.exit(0)
        
        elif sys.argv[1] == "help":
            print_help()
            sys.exit(0)
        
        else:
            print("Usage:")
            print("  python campaign_validator.py                    # Interactive mode")
            print("  python campaign_validator.py validate [file]    # Validate campaign(s)")
            print("  python campaign_validator.py list               # List campaigns")
            print("  python campaign_validator.py help               # Show help")
            sys.exit(1)
    
    # Interactive mode
    else:
        main()
