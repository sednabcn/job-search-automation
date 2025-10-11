#!/usr/bin/env python3
"""
Unified Keyword Extractor for All Job Boards
Extracts keywords from LinkedIn, Glassdoor, Reed, and Indeed
Automatically updates job-manager-config.yml and feeds into GitHub Actions
"""

import json
import yaml
import re
import logging
import argparse
import sys
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobBoard(Enum):
    """Supported job boards"""
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    REED = "reed"
    INDEED = "indeed"


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Task:
    """Task data structure"""
    id: str
    name: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: str
    due_date: str
    assigned_to: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority.name,
            'created_at': self.created_at,
            'due_date': self.due_date,
            'assigned_to': self.assigned_to,
            'dependencies': self.dependencies,
            'tags': self.tags
        }


@dataclass
class JobBoardStats:
    """Statistics for a single job board"""
    board: JobBoard
    total_jobs: int
    matching_jobs: int
    unique_companies: int
    salary_coverage: float  # percentage with salary info
    avg_match_score: float


class UnifiedKeywordExtractor:
    """Extract and analyze keywords from all job boards"""
    
    # Comprehensive tech skills database
    TECH_KEYWORDS = {
        'languages': [
            'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust',
            'ruby', 'php', 'scala', 'kotlin', 'swift', 'objective-c', 'dart', 'r',
            'elixir', 'haskell', 'clojure'
        ],
        'frameworks': [
            'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'spring',
            'spring boot', 'express', 'next.js', 'nestjs', 'laravel', 'rails',
            'asp.net', 'blazor', '.net core'
        ],
        'databases': [
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb',
            'cassandra', 'oracle', 'sql server', 'neo4j', 'firebase', 'mariadb',
            'couchdb', 'memcached', 'influxdb'
        ],
        'cloud': [
            'aws', 'azure', 'gcp', 'google cloud', 'cloud computing', 'serverless',
            'lambda', 'cloudflare', 'heroku', 'digital ocean'
        ],
        'devops': [
            'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'gitlab',
            'github', 'circleci', 'travis ci', 'github actions', 'ci/cd', 'helm',
            'vagrant', 'puppet', 'chef'
        ],
        'architecture': [
            'microservices', 'distributed systems', 'event-driven', 'rest api',
            'graphql', 'grpc', 'soap', 'message queues', 'rabbitmq', 'kafka',
            'event sourcing', 'cqrs'
        ],
        'monitoring': [
            'prometheus', 'grafana', 'datadog', 'newrelic', 'splunk', 'elk stack',
            'sentry', 'appdynamics', 'dynatrace'
        ],
        'methodologies': [
            'agile', 'scrum', 'kanban', 'tdd', 'bdd', 'continuous integration',
            'continuous delivery', 'continuous deployment', 'devops', 'lean'
        ],
        'testing': [
            'unit testing', 'integration testing', 'e2e testing', 'pytest', 'jest',
            'mocha', 'rspec', 'junit', 'selenium', 'cypress'
        ]
    }
    
    # Soft skills keywords
    SOFT_SKILLS = [
        'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
        'mentoring', 'collaboration', 'innovation', 'creative', 'adaptable',
        'initiative', 'accountability', 'strategic thinking', 'ownership'
    ]
    
    # Red flags to exclude
    RED_FLAGS = [
        'unpaid', 'no salary', 'commission only', 'entry level', 'junior',
        'graduate', 'intern', 'must relocate', 'scam', 'spam', 'work from home scam'
    ]
    
    def __init__(self, job_positions: List[str]):
        self.job_positions = job_positions
        self.all_keywords = defaultdict(Counter)
        self.salary_data = defaultdict(list)  # by board
        self.locations = Counter()
        self.companies = Counter()
        self.required_skills = Counter()
        self.preferred_skills = Counter()
        self.platform_stats: Dict[JobBoard, JobBoardStats] = {}
        self.job_matches = defaultdict(list)  # by platform
        
    def load_jobs_from_all_boards(self, file_mapping: Dict[JobBoard, str]) -> Dict[JobBoard, List[Dict]]:
        """Load job listings from all four platforms"""
        all_jobs = {}
        
        for board, filepath in file_mapping.items():
            if filepath and Path(filepath).exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        jobs = json.load(f)
                        if isinstance(jobs, list):
                            for job in jobs:
                                job['_source_platform'] = board.value
                            all_jobs[board] = jobs
                            logger.info(f"Loaded {len(jobs)} jobs from {board.value}")
                        else:
                            all_jobs[board] = [jobs]
                except Exception as e:
                    logger.error(f"Error loading {board.value} jobs from {filepath}: {str(e)}")
                    all_jobs[board] = []
            else:
                logger.warning(f"File not found for {board.value}: {filepath}")
                all_jobs[board] = []
        
        return all_jobs
    
    def filter_by_job_positions(self, jobs: Dict[JobBoard, List[Dict]]) -> Dict[JobBoard, List[Dict]]:
        """Filter jobs by target positions across all platforms"""
        filtered = {}
        
        for board, job_list in jobs.items():
            filtered[board] = []
            
            for job in job_list:
                job_title = job.get('title', '').lower()
                
                for position in self.job_positions:
                    if self._fuzzy_match(position.lower(), job_title):
                        filtered[board].append(job)
                        self.job_matches[board].append(job)
                        break
            
            logger.info(f"Filtered {len(filtered[board])} jobs matching target positions from {board.value}")
        
        return filtered
    
    def _fuzzy_match(self, pattern: str, text: str, threshold: float = 0.6) -> bool:
        """Fuzzy match job title pattern"""
        pattern_words = set(pattern.split())
        text_words = set(text.split())
        
        if not pattern_words:
            return True
        
        matches = len(pattern_words & text_words)
        return matches / len(pattern_words) >= threshold
    
    def extract_keywords(self, jobs_by_board: Dict[JobBoard, List[Dict]]):
        """Extract and categorize keywords from all job boards"""
        for board, jobs in jobs_by_board.items():
            logger.info(f"Analyzing {len(jobs)} jobs from {board.value}...")
            
            for job in jobs:
                # Check for red flags
                full_text = ' '.join([
                    job.get('title', ''),
                    job.get('description', ''),
                    job.get('description_snippet', ''),
                    job.get('summary', ''),
                    ' '.join(job.get('attributes', []))
                ]).lower()
                
                if any(flag in full_text for flag in self.RED_FLAGS):
                    continue
                
                # Extract technical keywords by category
                for category, keywords in self.TECH_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in full_text:
                            self.all_keywords[category][keyword] += 1
                
                # Extract soft skills
                for skill in self.SOFT_SKILLS:
                    if skill in full_text:
                        self.all_keywords['soft_skills'][skill] += 1
                
                # Categorize as required vs preferred
                description = job.get('description', '').lower()
                
                if any(req in description for req in ['required', 'must have', 'must', 'essential']):
                    for category, keywords in self.TECH_KEYWORDS.items():
                        for keyword in keywords:
                            if keyword in description:
                                self.required_skills[keyword] += 1
                
                if any(pref in description for pref in ['preferred', 'nice to have', 'bonus', 'plus']):
                    for category, keywords in self.TECH_KEYWORDS.items():
                        for keyword in keywords:
                            if keyword in description:
                                self.preferred_skills[keyword] += 1
                
                # Extract salary
                salary = job.get('salary', '')
                if salary:
                    salary_nums = self._extract_salary_range(salary, board)
                    if salary_nums:
                        self.salary_data[board].append(salary_nums)
                
                # Track locations and companies
                location = job.get('location', '').strip()
                if location:
                    self.locations[location] += 1
                
                company = job.get('company', '').strip()
                if company and company.lower() != 'unknown':
                    self.companies[company] += 1
    
    def _extract_salary_range(self, salary_text: str, board: JobBoard) -> Optional[Dict]:
        """Extract numeric salary values"""
        try:
            cleaned = re.sub(r'[£$€,]', '', salary_text.lower())
            numbers = re.findall(r'\d+(?:\.\d+)?', cleaned)
            numbers = [float(n) for n in numbers if n]
            
            if numbers:
                if 'k' in cleaned:
                    numbers = [n * 1000 if n < 1000 else n for n in numbers]
                
                currency = 'GBP' if '£' in salary_text or board in [JobBoard.REED] else 'USD'
                
                return {
                    'min': int(min(numbers)),
                    'max': int(max(numbers)),
                    'currency': currency
                }
        except Exception as e:
            logger.debug(f"Error parsing salary for {board.value}: {salary_text}")
        
        return None
    
    def get_top_keywords(self, category: str, top_n: int = 15) -> List[str]:
        """Get most common keywords in a category"""
        return [kw for kw, count in self.all_keywords[category].most_common(top_n)]
    
    def get_salary_stats(self) -> Dict:
        """Calculate salary statistics across all boards"""
        all_salaries = []
        for board_salaries in self.salary_data.values():
            all_salaries.extend(board_salaries)
        
        if not all_salaries:
            return {'minimum': 50000, 'currency': 'GBP', 'period': 'yearly'}
        
        all_mins = [s['min'] for s in all_salaries]
        all_maxs = [s['max'] for s in all_salaries]
        
        return {
            'minimum': int(sum(all_mins) / len(all_mins)) if all_mins else 50000,
            'maximum': int(sum(all_maxs) / len(all_maxs)) if all_maxs else 100000,
            'currency': 'GBP',
            'period': 'yearly'
        }
    
    def calculate_board_stats(self, total_jobs: Dict[JobBoard, int]) -> Dict[JobBoard, JobBoardStats]:
        """Calculate statistics for each job board"""
        stats = {}
        
        for board in JobBoard:
            matching = len(self.job_matches[board])
            total = total_jobs.get(board, 0)
            
            salary_with_info = len(self.salary_data[board])
            salary_coverage = (salary_with_info / matching * 100) if matching > 0 else 0
            
            companies = len(set(job.get('company') for job in self.job_matches[board]))
            
            stats[board] = JobBoardStats(
                board=board,
                total_jobs=total,
                matching_jobs=matching,
                unique_companies=companies,
                salary_coverage=salary_coverage,
                avg_match_score=0.0  # Would be calculated during matching
            )
        
        return stats
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'positions_analyzed': self.job_positions,
            'board_stats': {
                board.value: {
                    'total_jobs': stats.total_jobs,
                    'matching_jobs': stats.matching_jobs,
                    'unique_companies': stats.unique_companies,
                    'salary_coverage': f"{stats.salary_coverage:.1f}%"
                }
                for board, stats in self.platform_stats.items()
            },
            'salary_stats': self.get_salary_stats(),
            'top_locations': [loc for loc, _ in self.locations.most_common(15)],
            'top_companies': [company for company, _ in self.companies.most_common(20)],
            'keyword_analysis': {}
        }
        
        for category in self.TECH_KEYWORDS.keys():
            top = self.get_top_keywords(category, 15)
            if top:
                report['keyword_analysis'][category] = {
                    'top_keywords': top,
                    'frequency': [count for _, count in self.all_keywords[category].most_common(15)]
                }
        
        return report
    
    def generate_config(self, output_file: str = 'job-manager-config.yml') -> Dict:
        """Generate updated configuration file"""
        # Get top skills, preferring required over preferred
        top_required = [k for k, _ in self.required_skills.most_common(12)]
        if not top_required or len(top_required) < 8:
            # Fill in from all keywords if not enough required
            all_skills = Counter()
            for category in self.TECH_KEYWORDS.keys():
                for kw, count in self.all_keywords[category].most_common(5):
                    all_skills[kw] += count
            top_required.extend([k for k, _ in all_skills.most_common(12) if k not in top_required])
            top_required = top_required[:12]
        
        top_preferred = [k for k, _ in self.preferred_skills.most_common(12)]
        if not top_preferred:
            # Use devops and framework keywords as preferred
            devops_kws = self.get_top_keywords('devops', 8)
            framework_kws = self.get_top_keywords('frameworks', 4)
            top_preferred = devops_kws + framework_kws
        
        salary_stats = self.get_salary_stats()
        
        config = {
            'search': {
                'target_roles': self.job_positions,
                'required_keywords': list(set(top_required[:12])),
                'preferred_keywords': list(set(top_preferred[:12])),
                'exclude_keywords': self.RED_FLAGS[:10],
                'locations': [loc for loc, _ in self.locations.most_common(10)],
                'salary': salary_stats,
                'job_types': ['Full-time', 'Contract'],
                'experience_levels': ['Mid-Senior level', 'Senior level', 'Executive']
            },
            'matching': {
                'threshold': 75,
                'weights': {
                    'title_match': 25,
                    'skills_match': 30,
                    'location_match': 15,
                    'salary_match': 20,
                    'company_culture': 10
                }
            },
            'generated_at': datetime.now().isoformat(),
            'metadata': {
                'extracted_from': ['linkedin', 'glassdoor', 'reed', 'indeed'],
                'total_jobs_analyzed': sum(s.total_jobs for s in self.platform_stats.values()),
                'total_matches': sum(s.matching_jobs for s in self.platform_stats.values())
            }
        }
        
        try:
            with open(output_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration written to {output_file}")
        except Exception as e:
            logger.error(f"Error writing config: {str(e)}")
            return None
        
        return config
    
    def get_category_for_keyword(self, keyword: str) -> str:
        """Find category for a keyword"""
        for category, keywords in self.TECH_KEYWORDS.items():
            if keyword in keywords:
                return category
        return 'unknown'


class JobTaskManager:
    """Manage job search tasks"""
    
    def __init__(self, task_file: str = 'job_tasks.json'):
        self.task_file = task_file
        self.tasks = self._load_tasks()
    
    def _load_tasks(self) -> Dict[str, Task]:
        """Load tasks from file"""
        if Path(self.task_file).exists():
            try:
                with open(self.task_file, 'r') as f:
                    data = json.load(f)
                    return {
                        task_id: self._dict_to_task(task_data)
                        for task_id, task_data in data.items()
                    }
            except Exception as e:
                logger.error(f"Error loading tasks: {str(e)}")
        return {}
    
    def _dict_to_task(self, data: Dict) -> Task:
        """Convert dict to Task object"""
        return Task(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            status=TaskStatus(data['status']),
            priority=TaskPriority[data['priority']],
            created_at=data['created_at'],
            due_date=data['due_date'],
            assigned_to=data['assigned_to'],
            dependencies=data.get('dependencies', []),
            tags=data.get('tags', [])
        )
    
    def create_task(self, name: str, description: str,
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   due_date: str = None,
                   dependencies: List[str] = None,
                   tags: List[str] = None) -> Task:
        """Create new task"""
        task_id = hashlib.md5(
            f"{name}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        if due_date is None:
            due_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        task = Task(
            id=task_id,
            name=name,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.now().isoformat(),
            due_date=due_date,
            assigned_to='job_search_bot',
            dependencies=dependencies or [],
            tags=tags or []
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        logger.info(f"Created task: {task_id} - {name}")
        return task
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self._save_tasks()
            logger.info(f"Task {task_id} status updated to {status.value}")
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with given status"""
        return [t for t in self.tasks.values() if t.status == status]
    
    def _save_tasks(self):
        """Save tasks to file"""
        try:
            with open(self.task_file, 'w') as f:
                json.dump(
                    {tid: t.to_dict() for tid, t in self.tasks.items()},
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Error saving tasks: {str(e)}")
    
    def generate_task_report(self) -> Dict:
        """Generate task summary report"""
        return {
            'total_tasks': len(self.tasks),
            'pending': len(self.get_tasks_by_status(TaskStatus.PENDING)),
            'in_progress': len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS)),
            'completed': len(self.get_tasks_by_status(TaskStatus.COMPLETED)),
            'failed': len(self.get_tasks_by_status(TaskStatus.FAILED))
        }


def main():
    parser = argparse.ArgumentParser(
        description='Unified Keyword Extractor for All Job Boards'
    )
    parser.add_argument('--positions', nargs='+',
                       default=['Senior Software Engineer', 'Staff Engineer', 'Tech Lead'],
                       help='Job positions to analyze')
    parser.add_argument('--linkedin', type=str,
                       help='LinkedIn jobs JSON file')
    parser.add_argument('--glassdoor', type=str,
                       help='Glassdoor jobs JSON file')
    parser.add_argument('--reed', type=str,
                       help='Reed jobs JSON file')
    parser.add_argument('--indeed', type=str,
                       help='Indeed jobs JSON file')
    parser.add_argument('--output-config', type=str,
                       default='job-manager-config.yml',
                       help='Output config file')
    parser.add_argument('--output-report', type=str,
                       help='Output analysis report as JSON')
    parser.add_argument('--report', action='store_true',
                       help='Generate and print analysis report')
    parser.add_argument('--create-tasks', action='store_true',
                       help='Create job search tasks')
    parser.add_argument('--github-output', action='store_true',
                       help='Set GitHub Actions output variables')
    
    args = parser.parse_args()
    
    # Extract keywords from all boards
    extractor = UnifiedKeywordExtractor(args.positions)
    
    # Map file arguments to job boards
    file_mapping = {
        JobBoard.LINKEDIN: args.linkedin,
        JobBoard.GLASSDOOR: args.glassdoor,
        JobBoard.REED: args.reed,
        JobBoard.INDEED: args.indeed
    }
    
    # Remove None values
    file_mapping = {k: v for k, v in file_mapping.items() if v}
    
    if not file_mapping:
        logger.error("No job board files provided")
        sys.exit(1)
    
    # Load and process jobs
    all_jobs = extractor.load_jobs_from_all_boards(file_mapping)
    total_jobs = {board: len(jobs) for board, jobs in all_jobs.items()}
    
    filtered_jobs = extractor.filter_by_job_positions(all_jobs)
    extractor.extract_keywords(filtered_jobs)
    extractor.platform_stats = extractor.calculate_board_stats(total_jobs)
    
    # Generate config
    config = extractor.generate_config(args.output_config)
    
    if config:
        logger.info(f"Successfully updated {args.output_config}")
    
    # Generate and save report
    if args.report or args.output_report:
        report = extractor.generate_report()
        
        if args.report:
            print("\n" + "="*80)
            print("KEYWORD EXTRACTION REPORT")
            print("="*80)
            print(json.dumps(report, indent=2))
        
        if args.output_report:
            with open(args.output_report, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report written to {args.output_report}")
    
    # Create tasks if requested
    if args.create_tasks:
        manager = JobTaskManager()
        
        task1 = manager.create_task(
            name='Extract Keywords from All Boards',
            description='Extract keywords from LinkedIn, Glassdoor, Reed, and Indeed',
            priority=TaskPriority.CRITICAL,
            tags=['keyword-extraction', 'multi-platform']
        )
        
        task2 = manager.create_task(
            name='Update job-manager-config.yml',
            description='Update job-manager-config.yml with extracted keywords and match requirements',
            priority=TaskPriority.HIGH,
            dependencies=[task1.id],
            tags=['configuration', 'automation']
        )
        
        task3 = manager.create_task(
            name='Multi-Platform Job Discovery',
            description='Execute job discovery across all platforms using updated config',
            priority=TaskPriority.HIGH,
            dependencies=[task2.id],
            tags=['discovery', 'matching']
        )
        
        task4 = manager.create_task(
            name='Generate Analytics Report',
            description='Generate and store keyword analytics report',
            priority=TaskPriority.MEDIUM,
            dependencies=[task1.id],
            tags=['reporting', 'analytics']
        )
        
        print("\nTasks created:")
        print(json.dumps(manager.generate_task_report(), indent=2))
    
    # GitHub Actions output
    if args.github_output:
        print(f"\n::set-output name=config_file::{args.output_config}")
        if args.output_report:
            print(f"::set-output name=report_file::{args.output_report}")
        print(f"::set-output name=total_matches::{sum(s.matching_jobs for s in extractor.platform_stats.values())}")


if __name__ == '__main__':
    main()
