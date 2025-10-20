#!/usr/bin/env python3
"""
Professional Job Search Command Center - CLI
Fully integrated with GitHub Actions workflow
Supports both interactive and automation modes
"""

import sys
import json
import yaml
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import re


class JobSearchTracker:
    """Track all job applications and their status"""
    
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
        self.applications_file = self.tracking_dir / "applications.json"
        self.applications = self._load_applications()
    
    def _load_applications(self) -> List[Dict]:
        if not self.applications_file.exists():
            return []
        with open(self.applications_file, 'r') as f:
            return json.load(f)
    
    def _save_applications(self):
        with open(self.applications_file, 'w') as f:
            json.dump(self.applications, f, indent=2)
    
    def add_application(self, company: str, position: str, url: str, 
                       source: str, **kwargs) -> str:
        """Add new application with automation support"""
        app_id = f"{company.lower().replace(' ', '_')}_{len(self.applications) + 1}"
        
        application = {
            'id': app_id,
            'company': company,
            'position': position,
            'url': url,
            'source': source,
            'applied_date': datetime.now().isoformat(),
            'status': 'applied',
            'timeline': [{
                'date': datetime.now().isoformat(),
                'event': 'applied',
                'notes': 'Application submitted'
            }],
            **kwargs
        }
        
        self.applications.append(application)
        self._save_applications()
        return app_id
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        if not self.applications:
            return {
                'total_applications': 0,
                'by_status': {},
                'by_source': {},
                'response_rate': 0
            }
        
        status_counts = Counter(app['status'] for app in self.applications)
        source_counts = Counter(app['source'] for app in self.applications)
        
        response_count = sum(
            status_counts.get(s, 0) 
            for s in ['phone_screen', 'interview', 'offer']
        )
        
        return {
            'total_applications': len(self.applications),
            'by_status': dict(status_counts),
            'by_source': dict(source_counts),
            'response_rate': (response_count / len(self.applications)) * 100
        }


class KeywordExtractor:
    """Extract keywords from job descriptions for config generation"""
    
    def __init__(self):
        self.tech_keywords = {
            'languages': ['python', 'javascript', 'java', 'typescript', 'go', 
                         'rust', 'c++', 'ruby', 'php', 'swift', 'kotlin'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 
                          'spring', 'express', 'fastapi', 'rails'],
            'cloud': ['aws', 'azure', 'gcp', 'kubernetes', 'docker', 
                     'terraform', 'jenkins', 'ci/cd'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 
                         'elasticsearch', 'dynamodb'],
            'tools': ['git', 'jira', 'confluence', 'slack', 'linux', 
                     'agile', 'scrum']
        }
    
    def extract_from_jobs(self, job_files: List[Path], 
                         target_positions: List[str]) -> Dict:
        """
        Extract keywords from multiple job board JSON files
        Returns structured data for config generation
        """
        all_jobs = []
        board_stats = {}
        
        # Load all job data
        for job_file in job_files:
            if not job_file.exists():
                continue
                
            board_name = job_file.stem.replace('_jobs', '')
            
            try:
                with open(job_file, 'r') as f:
                    jobs = json.load(f)
                    if isinstance(jobs, dict):
                        jobs = jobs.get('jobs', [])
                    
                    board_stats[board_name] = {
                        'total_jobs': len(jobs),
                        'matching_jobs': 0,
                        'unique_companies': len(set(j.get('company', '') for j in jobs))
                    }
                    all_jobs.extend(jobs)
            except Exception as e:
                print(f"Warning: Could not load {job_file}: {e}")
        
        # Filter relevant jobs
        matching_jobs = self._filter_relevant_jobs(all_jobs, target_positions)
        
        # Extract keywords by category
        keyword_analysis = self._analyze_keywords(matching_jobs)
        
        # Extract locations and companies
        locations = self._extract_locations(matching_jobs)
        companies = self._extract_companies(matching_jobs)
        
        # Extract salary info
        salary_stats = self._extract_salary_info(matching_jobs)
        
        # Update board stats
        for job in matching_jobs:
            board = job.get('source', 'unknown')
            if board in board_stats:
                board_stats[board]['matching_jobs'] += 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'positions_analyzed': target_positions,
            'total_jobs': len(all_jobs),
            'matching_jobs': len(matching_jobs),
            'board_stats': board_stats,
            'keyword_analysis': keyword_analysis,
            'top_locations': locations[:10],
            'top_companies': companies[:15],
            'salary_stats': salary_stats
        }
    
    def _filter_relevant_jobs(self, jobs: List[Dict], 
                             positions: List[str]) -> List[Dict]:
        """Filter jobs matching target positions"""
        matching = []
        position_patterns = [re.compile(p, re.IGNORECASE) for p in positions]
        
        for job in jobs:
            title = job.get('title', '') or job.get('position', '')
            if any(pattern.search(title) for pattern in position_patterns):
                matching.append(job)
        
        return matching
    
    def _analyze_keywords(self, jobs: List[Dict]) -> Dict:
        """Extract and count keywords by category"""
        keyword_counts = defaultdict(Counter)
        
        for job in jobs:
            # Combine all text fields
            text = ' '.join([
                str(job.get('title', '')),
                str(job.get('description', '')),
                str(job.get('requirements', ''))
            ]).lower()
            
            # Count keywords by category
            for category, keywords in self.tech_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        keyword_counts[category][keyword] += 1
        
        # Get top keywords per category
        result = {}
        for category, counter in keyword_counts.items():
            result[category] = {
                'top_keywords': [k for k, v in counter.most_common(10)],
                'counts': dict(counter.most_common(10))
            }
        
        return result
    
    def _extract_locations(self, jobs: List[Dict]) -> List[str]:
        """Extract and rank locations"""
        locations = Counter()
        for job in jobs:
            loc = job.get('location', '')
            if loc and loc.lower() not in ['remote', 'n/a', '']:
                locations[loc] += 1
        
        return [loc for loc, count in locations.most_common()]
    
    def _extract_companies(self, jobs: List[Dict]) -> List[str]:
        """Extract unique companies"""
        companies = Counter()
        for job in jobs:
            company = job.get('company', '')
            if company:
                companies[company] += 1
        
        return [comp for comp, count in companies.most_common()]
    
    def _extract_salary_info(self, jobs: List[Dict]) -> Dict:
        """Extract salary statistics"""
        salaries = []
        for job in jobs:
            salary = job.get('salary', '')
            if salary and isinstance(salary, (int, float)):
                salaries.append(salary)
            elif isinstance(salary, str):
                # Try to extract numbers from salary strings
                numbers = re.findall(r'\d+', salary.replace(',', ''))
                if numbers:
                    salaries.append(int(numbers[0]))
        
        if not salaries:
            return {'minimum': 0, 'maximum': 0, 'currency': 'GBP', 'period': 'year'}
        
        return {
            'minimum': min(salaries),
            'maximum': max(salaries),
            'average': sum(salaries) // len(salaries),
            'currency': 'GBP',
            'period': 'year'
        }
    
    def generate_config(self, analysis: Dict, output_file: Path):
        """Generate job-manager-config.yml from analysis"""
        
        # Extract top keywords across all categories
        all_keywords = []
        for category_data in analysis['keyword_analysis'].values():
            all_keywords.extend(category_data['top_keywords'][:5])
        
        # Build config structure
        config = {
            'search': {
                'target_roles': analysis['positions_analyzed'],
                'required_keywords': list(set(all_keywords[:15])),
                'preferred_keywords': list(set(all_keywords[15:30])),
                'locations': analysis['top_locations'][:8],
                'remote': True,
                'salary': {
                    'minimum': analysis['salary_stats']['minimum'],
                    'currency': analysis['salary_stats']['currency']
                }
            },
            'matching': {
                'min_score': 75,
                'required_match': 60,
                'preferred_bonus': 5,
                'location_bonus': 10
            },
            'generated_at': analysis['timestamp'],
            'metadata': {
                'total_jobs_analyzed': analysis['total_jobs'],
                'matching_jobs': analysis['matching_jobs'],
                'boards': list(analysis['board_stats'].keys())
            }
        }
        
        # Write YAML config
        with open(output_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Generated config: {output_file}")
        return config


class WorkflowIntegration:
    """GitHub Actions workflow integration"""
    
    @staticmethod
    def set_output(name: str, value: str):
        """Set GitHub Actions output"""
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"{name}={value}\n")
        print(f"::set-output name={name}::{value}")
    
    @staticmethod
    def generate_summary(analysis: Dict, config_file: Path) -> str:
        """Generate GitHub Actions job summary"""
        summary = f"""# 🤖 Keyword Extraction Complete

## 📊 Analysis Overview
- **Positions Analyzed**: {', '.join(analysis['positions_analyzed'])}
- **Total Jobs**: {analysis['total_jobs']}
- **Matching Jobs**: {analysis['matching_jobs']}
- **Timestamp**: {analysis['timestamp']}

## 📈 Board Statistics
"""
        
        for board, stats in analysis['board_stats'].items():
            summary += f"""
### {board.upper()}
- Total Jobs: {stats['total_jobs']}
- Matching: {stats['matching_jobs']}
- Companies: {stats['unique_companies']}
"""
        
        summary += f"""
## 🔑 Top Keywords Extracted
"""
        for category, data in analysis['keyword_analysis'].items():
            keywords = ', '.join(data['top_keywords'][:8])
            summary += f"- **{category.upper()}**: {keywords}\n"
        
        summary += f"""
## 🏙️ Top Locations
{', '.join(analysis['top_locations'][:10])}

## 💰 Salary Range
£{analysis['salary_stats']['minimum']:,} - £{analysis['salary_stats']['maximum']:,}/year

## ✅ Config Generated
`{config_file}`
"""
        return summary


def cmd_extract(args):
    """Extract keywords and generate config (workflow mode)"""
    print("🔍 Starting keyword extraction...")
    
    # Parse inputs
    positions = args.positions or ['Senior Software Engineer', 'Staff Engineer']
    
    # Find job files
    job_files = []
    for board in ['linkedin', 'glassdoor', 'reed', 'indeed']:
        file_arg = getattr(args, board, None)
        if file_arg:
            job_files.append(Path(file_arg))
    
    if not job_files:
        print("❌ No job files provided")
        sys.exit(1)
    
    # Extract keywords
    extractor = KeywordExtractor()
    analysis = extractor.extract_from_jobs(job_files, positions)
    
    # Generate config
    config_file = Path(args.output_config or 'job-manager-config.yml')
    extractor.generate_config(analysis, config_file)
    
    # Save analysis report
    if args.output_report:
        report_file = Path(args.output_report)
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"✅ Report saved: {report_file}")
    
    # Generate summary for GitHub Actions
    if args.github_output:
        summary = WorkflowIntegration.generate_summary(analysis, config_file)
        if 'GITHUB_STEP_SUMMARY' in os.environ:
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'w') as f:
                f.write(summary)
        
        # Set outputs
        WorkflowIntegration.set_output('total_matches', str(analysis['matching_jobs']))
        WorkflowIntegration.set_output('config_generated', str(config_file))
    
    print("\n✅ Extraction complete!")
    return analysis


def cmd_dashboard(args):
    """Show interactive dashboard"""
    print("\n" + "="*70)
    print("  📊 JOB SEARCH DASHBOARD")
    print("="*70 + "\n")
    
    tracker = JobSearchTracker()
    stats = tracker.get_stats()
    
    print("📈 APPLICATION STATISTICS")
    print("-"*70)
    print(f"Total Applications: {stats['total_applications']}")
    print(f"Response Rate: {stats['response_rate']:.1f}%")
    print()
    
    if stats['by_status']:
        print("By Status:")
        for status, count in stats['by_status'].items():
            print(f"  • {status}: {count}")
        print()
    
    if stats['by_source']:
        print("By Source:")
        for source, count in stats['by_source'].items():
            print(f"  • {source}: {count}")


def cmd_apply(args):
    """Track new application"""
    tracker = JobSearchTracker()
    
    app_id = tracker.add_application(
        company=args.company,
        position=args.position,
        url=args.url,
        source=args.source,
        resume_version=args.resume_version or 'default',
        cover_letter=args.cover_letter,
        notes=args.notes or ''
    )
    
    print(f"\n✅ Application tracked: {app_id}")
    print(f"Company: {args.company}")
    print(f"Position: {args.position}")


def main():
    parser = argparse.ArgumentParser(
        description="Professional Job Search Command Center",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Extract command (workflow mode)
    extract_parser = subparsers.add_parser('extract', 
        help='Extract keywords from job boards')
    extract_parser.add_argument('--positions', nargs='+', 
        help='Target positions')
    extract_parser.add_argument('--linkedin', help='LinkedIn jobs JSON')
    extract_parser.add_argument('--glassdoor', help='Glassdoor jobs JSON')
    extract_parser.add_argument('--reed', help='Reed jobs JSON')
    extract_parser.add_argument('--indeed', help='Indeed jobs JSON')
    extract_parser.add_argument('--output-config', 
        default='job-manager-config.yml', help='Output config file')
    extract_parser.add_argument('--output-report', 
        help='Output analysis report JSON')
    extract_parser.add_argument('--github-output', action='store_true',
        help='Generate GitHub Actions outputs')
    extract_parser.add_argument('--report', action='store_true',
        help='Generate detailed report')
    
    # Dashboard command (interactive mode)
    subparsers.add_parser('dashboard', help='Show dashboard')
    
    # Apply command (track application)
    apply_parser = subparsers.add_parser('apply', 
        help='Track new application')
    apply_parser.add_argument('--company', required=True)
    apply_parser.add_argument('--position', required=True)
    apply_parser.add_argument('--url', required=True)
    apply_parser.add_argument('--source', required=True)
    apply_parser.add_argument('--resume-version')
    apply_parser.add_argument('--cover-letter', action='store_true')
    apply_parser.add_argument('--notes')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'extract':
            cmd_extract(args)
        elif args.command == 'dashboard':
            cmd_dashboard(args)
        elif args.command == 'apply':
            cmd_apply(args)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()
