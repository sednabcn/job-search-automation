#!/usr/bin/env python3
import json
import yaml
import re
from collections import Counter, defaultdict
from typing import List, Dict
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeywordExtractor:
    """Extract and analyze keywords from job listings"""
    
    TECH_KEYWORDS = {
        'languages': ['python', 'javascript', 'java', 'c++', 'go', 'rust', 'ruby', 'php', 'typescript', 'scala', 'kotlin'],
        'frameworks': ['react', 'vue', 'angular', 'django', 'flask', 'spring', 'express', 'fastapi', 'node.js', 'next.js'],
        'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'cassandra', 'oracle'],
        'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'cloud computing', 'serverless'],
        'devops': ['docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'gitlab', 'github actions', 'ci/cd'],
        'architecture': ['microservices', 'distributed systems', 'event-driven', 'rest api', 'graphql', 'grpc'],
        'methodologies': ['agile', 'scrum', 'kanban', 'tdd', 'continuous integration', 'continuous delivery']
    }

    SOFT_SKILLS = [
        'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
        'mentoring', 'collaboration', 'innovation', 'creative', 'adaptable'
    ]
    
    RED_FLAGS = [
        'unpaid', 'no salary', 'commission only', 'work from home scam',
        'entry level', 'junior', 'graduate', 'intern', 'must relocate'
    ]

    def __init__(self, job_positions: List[str]):
        self.job_positions = job_positions
        self.all_keywords = defaultdict(Counter)
        self.required_skills = Counter()
        self.preferred_skills = Counter()
        self.locations = Counter()
        self.salary_data = []
        self.analysis_results = {}

    def load_jobs_from_files(self, file_patterns: List[str]) -> List[Dict]:
        all_jobs = []
        for pattern in file_patterns:
            files = list(Path('.').glob(pattern))
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        jobs = json.load(f)
                        if isinstance(jobs, list):
                            all_jobs.extend(jobs)
                            logger.info(f"Loaded {len(jobs)} jobs from {file_path}")
                        else:
                            all_jobs.append(jobs)
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {str(e)}")
        return all_jobs

    def extract_keywords(self, jobs: List[Dict]):
        logger.info(f"Analyzing {len(jobs)} job listings...")
        for job in jobs:
            text_fields = [
                job.get('title', ''),
                job.get('description_snippet', ''),
                job.get('full_description', ''),
                ' '.join(job.get('attributes', [])),
                job.get('job_type', '')
            ]
            full_text = ' '.join(text_fields).lower()

            for category, keywords in self.TECH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in full_text:
                        self.all_keywords[category][keyword] += 1

            for skill in self.SOFT_SKILLS:
                if skill in full_text:
                    self.all_keywords['soft_skills'][skill] += 1

            if 'required' in full_text or 'must have' in full_text:
                for category, keywords in self.TECH_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in full_text:
                            self.required_skills[keyword] += 1

            if 'preferred' in full_text or 'nice to have' in full_text or 'bonus' in full_text:
                for category, keywords in self.TECH_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in full_text:
                            self.preferred_skills[keyword] += 1

            # Salary
            salary = job.get('salary', '')
            if salary:
                salary_range = self._extract_salary_range(salary)
                if salary_range:
                    self.salary_data.append(salary_range)

            # Locations
            loc = job.get('location', '').strip()
            if loc:
                self.locations[loc] += 1

    def _extract_salary_range(self, salary_text: str) -> Dict:
        try:
            cleaned = re.sub(r'[£$€,]', '', salary_text.lower())
            numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', cleaned)
            numbers = [float(n.replace(',', '')) for n in numbers]
            if numbers and 'k' in cleaned:
                numbers = [n*1000 if n < 1000 else n for n in numbers]
            if numbers:
                return {'min': min(numbers), 'max': max(numbers), 'currency': 'GBP' if '£' in salary_text else 'USD'}
        except Exception:
            return None
        return None

    def get_top_keywords(self, category: str, top_n: int = 10) -> List[str]:
        return [kw for kw, _ in self.all_keywords[category].most_common(top_n)]

    def get_salary_stats(self) -> Dict:
        if not self.salary_data:
            return {'minimum': 50000, 'maximum': 100000, 'currency': 'GBP', 'period': 'yearly'}
        mins = [s['min'] for s in self.salary_data if s]
        maxs = [s['max'] for s in self.salary_data if s]
        return {'minimum': int(sum(mins)/len(mins)), 'maximum': int(sum(maxs)/len(maxs)), 'currency': 'GBP', 'period': 'yearly'}

    def analyze_jobs(self, jobs: List[Dict]):
        """Full analysis pipeline"""
        self.extract_keywords(jobs)
        self.analysis_results = {
            'positions_analyzed': self.job_positions,
            'total_jobs': len(jobs),
            'matching_jobs': sum(
                1 for job in jobs
                if any(pos.lower() in job.get('title', '').lower() for pos in self.job_positions)
            ),
            'top_keywords': {cat: [kw for kw, _ in counter.most_common(5)] for cat, counter in self.all_keywords.items()},
            'top_locations': [loc for loc, _ in self.locations.most_common(5)],
            'salary_stats': self.get_salary_stats()
        }

    def export_analysis_report(self, output_file: str):
        if not self.analysis_results:
            logger.warning("No analysis results found, creating empty report")
            self.analysis_results = {}
        with open(output_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        logger.info(f"Analysis report exported to {output_file}")

    def generate_config(self, output_file: str = 'job-manager-config.yml'):
        top_required = [k for k, _ in self.required_skills.most_common(10)]
        top_preferred = [k for k, _ in self.preferred_skills.most_common(10)]
        top_locations = [loc for loc, _ in self.locations.most_common(10)]

        CONFIG_TEMPLATE = {
            'search': {
                'linkedin': {
                    'enabled': True,
                    'url': 'https://linkedin.com/jobs/search',
                    'filters': ['title', 'location', 'experience']
                },
                'glassdoor': {
                    'enabled': True,
                    'url': 'https://glassdoor.com/jobs',
                    'filters': ['title', 'location']
                },
                'indeed': {
                    'enabled': True,
                    'url': 'https://indeed.com/jobs',
                    'filters': ['title', 'company']
                }
            },
            'output': {
                'report_format': 'json',
                'update_frequency': 'weekly'
            }
        }

        CONFIG_TEMPLATE['search'].update({
            'target_roles': self.job_positions,
            'required_keywords': top_required,
            'preferred_keywords': top_preferred,
            'locations': top_locations
        })

        with open(output_file, 'w') as f:
            yaml.safe_dump(CONFIG_TEMPLATE, f)
        logger.info(f"Configuration saved to {output_file}")
