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
    
    # Check if campaign results exist
    if not Path(args.campaign_results).exists():
        print(f"⚠️  Campaign results not found: {args.campaign_results}")
        print("Creating empty results structure...")
        
        # Create empty results
        empty_results = {
            'campaigns': [],
            'total_applications': 0,
            'successful': 0,
            'failed': 0
        }
        
        # Save output
        with open(args.output, 'w') as f:
            json.dump({
                'status_updates': 0,
                'message': 'No campaign results to process'
            }, f, indent=2)
        
        print("✅ No updates needed")
        return 0
    
    # Load campaign results
    with open(args.campaign_results, 'r') as f:
        campaign_results = json.load(f)
    
    # Initialize updater
    updater = GitHubActionsUpdater(args.data_dir)
    
    # Process status updates
    updates_count = updater.process_campaign_results(campaign_results)
    
    # Save results
    result = {
        'status_updates': updates_count,
        'message': f'Updated {updates_count} application statuses'
    }
    
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Updated {updates_count} application statuses")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
