#!/usr/bin/env python3
"""
GitHub Actions wrapper for application status updates
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from update_application_status import GitHubActionsUpdater

def main():
    """Main execution for GitHub Actions"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign-results', required=True, help='Campaign results JSON file')
    parser.add_argument('--data-dir', default='job_search', help='Data directory')
    parser.add_argument('--output', default='status_update_results.json', help='Output file')
    
    args = parser.parse_args()
    
    # Load campaign results
    with open(args.campaign_results, 'r') as f:
        campaign_results = json.load(f)
    
    # Initialize updater
    updater = GitHubActionsUpdater(args.data_dir)
    
    # Perform updates
    results = updater.auto_update_from_campaign(campaign_results)
    
    # Generate summary
    summary = updater.generate_github_summary()
    
    # Save results
    output = {
        'updates': results,
        'summary_markdown': summary
    }
    
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print(summary)
    print(f"\nðŸ"Š Updates: {results['status_updates']}")
    print(f"â° Reminders: {results['reminders_created']}")
    
    if results['errors']:
        print(f"\nâš ï¸  Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    return 0 if not results['errors'] else 1

if __name__ == '__main__':
    sys.exit(main())
