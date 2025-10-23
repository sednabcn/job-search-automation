#!/usr/bin/env python3
"""
GitHub Actions wrapper for follow-up reminder management
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from follow_up_remainders import GitHubActionsFollowUpManager

def main():
    """Main execution for GitHub Actions"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['create', 'report', 'export'], required=True)
    parser.add_argument('--campaign-results', help='Campaign results JSON file')
    parser.add_argument('--data-dir', default='job_search', help='Data directory')
    parser.add_argument('--days-ahead', type=int, default=7, help='Days ahead for report')
    parser.add_argument('--output', default='followup_output.json', help='Output file')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = GitHubActionsFollowUpManager(args.data_dir)
    
    if args.mode == 'create':
        # Create reminders from campaign results
        if not args.campaign_results:
            print("âŒ --campaign-results required for 'create' mode")
            return 1
        
        with open(args.campaign_results, 'r') as f:
            campaign_results = json.load(f)
        
        count = manager.auto_create_campaign_reminders(campaign_results)
        
        result = {
            'reminders_created': count,
            'message': f'Created {count} follow-up reminders'
        }
        
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"âœ… Created {count} reminders")
        
    elif args.mode == 'report':
        # Generate report
        report = manager.generate_github_actions_report(args.days_ahead)
        
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"ðŸ"Š Report generated:")
        print(f"  Due reminders: {report['summary']['due_reminders']}")
        print(f"  Follow-ups needed: {report['summary']['follow_ups_needed']}")
        print(f"  Critical: {report['summary']['critical_reminders']}")
        
    elif args.mode == 'export':
        # Export for email
        output_file = manager.export_for_email(args.output)
        
        # Also generate text report
        text_report = manager.generate_follow_up_report(args.days_ahead)
        text_file = Path(args.data_dir) / 'reports' / 'followup_report.txt'
        text_file.parent.mkdir(parents=True, exist_ok=True)
        with open(text_file, 'w') as f:
            f.write(text_report)
        
        # Export calendar
        calendar_file = manager.export_to_calendar()
        
        print(f"âœ… Exported:")
        print(f"  JSON: {output_file}")
        print(f"  Text: {text_file}")
        print(f"  Calendar: {calendar_file}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
