#!/usr/bin/env python3
"""
Generate HTML email report from template
"""
import sys
import argparse
from pathlib import Path
from string import Template
from datetime import datetime

def generate_email_report(
    template_file: str,
    output_file: str,
    **kwargs
) -> str:
    """Generate email report from template"""
    
    # Read template
    template_path = Path(template_file)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_file}")
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Create Template object
    template = Template(template_content)
    
    # Add default values
    default_values = {
        'execution_date': datetime.now().strftime('%Y-%m-%d at %H:%M UTC'),
        'total_applications': 0,
        'successful': 0,
        'failed': 0,
        'high_quality_matches': 0,
        'top_score': 0,
        'packages_created': 0,
        'reminders_created': 0,
        'github_server': 'https://github.com',
        'repository': 'username/repo',
        'run_id': '0'
    }
    
    # Merge with provided kwargs
    default_values.update(kwargs)
    
    # Substitute values
    html_content = template.safe_substitute(**default_values)
    
    # Save to output file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Email report generated: {output_path}")
    print(f"   Template: {template_file}")
    print(f"   Size: {len(html_content)} bytes")
    
    return str(output_path)

def main():
    parser = argparse.ArgumentParser(description='Generate email report from template')
    parser.add_argument('--template', required=True, help='HTML template file')
    parser.add_argument('--output', default='email-body.html', help='Output HTML file')
    parser.add_argument('--total-applications', type=int, default=0)
    parser.add_argument('--successful', type=int, default=0)
    parser.add_argument('--failed', type=int, default=0)
    parser.add_argument('--high-quality-matches', type=int, default=0)
    parser.add_argument('--top-score', type=float, default=0)
    parser.add_argument('--packages-created', type=int, default=0)
    parser.add_argument('--reminders-created', type=int, default=0)
    parser.add_argument('--github-server', default='https://github.com')
    parser.add_argument('--repository', required=True)
    parser.add_argument('--run-id', required=True)
    
    args = parser.parse_args()
    
    # Convert args to dict
    template_vars = {
        'total_applications': args.total_applications,
        'successful': args.successful,
        'failed': args.failed,
        'high_quality_matches': args.high_quality_matches,
        'top_score': args.top_score,
        'packages_created': args.packages_created,
        'reminders_created': args.reminders_created,
        'github_server': args.github_server,
        'repository': args.repository,
        'run_id': args.run_id
    }
    
    generate_email_report(
        args.template,
        args.output,
        **template_vars
    )

if __name__ == '__main__':
    main()
