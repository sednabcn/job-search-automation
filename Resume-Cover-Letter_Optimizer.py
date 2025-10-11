"""
Resume & Cover Letter Optimizer
ATS-friendly optimization and A/B testing
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import Counter

class ATSOptimizer:
    """Optimize resumes for Applicant Tracking Systems"""
    
    def __init__(self):
        self.common_ats_keywords = self._load_common_keywords()
    
    def _load_common_keywords(self) -> Dict[str, List[str]]:
        """Common ATS keywords by field"""
        return {
            'software_engineering': [
                'python', 'java', 'javascript', 'react', 'node.js', 'aws', 'docker',
                'kubernetes', 'agile', 'scrum', 'ci/cd', 'git', 'sql', 'nosql',
                'microservices', 'rest api', 'testing', 'debugging'
            ],
            'data_science': [
                'python', 'r', 'sql', 'machine learning', 'deep learning', 'tensorflow',
                'pytorch', 'pandas', 'numpy', 'statistics', 'data visualization',
                'tableau', 'power bi', 'a/b testing', 'regression', 'classification'
            ],
            'project_management': [
                'pmp', 'agile', 'scrum', 'kanban', 'jira', 'stakeholder management',
                'budgeting', 'risk management', 'timeline management', 'cross-functional',
                'deliverables', 'milestones', 'kpi', 'roi'
            ],
            'marketing': [
                'seo', 'sem', 'google analytics', 'content marketing', 'social media',
                'email marketing', 'campaign management', 'roi', 'conversion rate',
                'a/b testing', 'copywriting', 'branding', 'market research'
            ],
            'education': [
                'curriculum development', 'lesson planning', 'assessment', 'differentiation',
                'classroom management', 'student engagement', 'learning outcomes',
                'educational technology', 'pedagogy', 'professional development'
            ]
        }
    
    def analyze_resume(self, resume_text: str, job_description: str = "") -> Dict:
        """
        Analyze resume for ATS compatibility
        
        Args:
            resume_text: Your resume text
            job_description: Target job description (optional)
            
        Returns:
            Analysis results with recommendations
        """
        issues = []
        warnings = []
        score = 100
        
        # Check for formatting issues
        if re.search(r'[│┌└├─┐┘┬┴┼]', resume_text):
            issues.append("Contains table borders - ATS may not parse correctly")
            score -= 15
        
        if len(re.findall(r'https?://', resume_text)) > 5:
            warnings.append("Many URLs - ensure they're formatted as plain text")
        
        # Check for required sections
        required_sections = ['experience', 'education', 'skills']
        for section in required_sections:
            if section.lower() not in resume_text.lower():
                issues.append(f"Missing '{section}' section")
                score -= 10
        
        # Check for contact info
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text):
            issues.append("No email address found")
            score -= 20
        
        # Check for quantifiable achievements
        numbers = re.findall(r'\d+%|\$\d+|increased|decreased|improved|reduced', resume_text.lower())
        if len(numbers) < 5:
            warnings.append("Add more quantifiable achievements (numbers, percentages, metrics)")
        
        # Check for action verbs
        action_verbs = ['led', 'managed', 'developed', 'implemented', 'created', 
                       'designed', 'improved', 'increased', 'reduced', 'achieved']
        verb_count = sum(1 for verb in action_verbs if verb in resume_text.lower())
        if verb_count < 8:
            warnings.append("Use more strong action verbs (led, managed, achieved, etc.)")
        
        # Match against job description
        keyword_match = 0
        matched_keywords = []
        missing_keywords = []
        
        if job_description:
            jd_lower = job_description.lower()
            resume_lower = resume_text.lower()
            
            # Extract keywords from job description
            jd_words = set(re.findall(r'\b\w+\b', jd_lower))
            important_words = [w for w in jd_words if len(w) > 4 and w not in 
                             ['with', 'have', 'will', 'should', 'could', 'about', 'their', 'there']]
            
            for word in important_words:
                if word in resume_lower:
                    matched_keywords.append(word)
                    keyword_match += 1
                else:
                    if word in ['python', 'java', 'sql', 'aws', 'docker', 'agile', 'scrum']:
                        missing_keywords.append(word)
            
            match_rate = (keyword_match / len(important_words) * 100) if important_words else 0
            
            if match_rate < 40:
                issues.append(f"Low keyword match with job description ({match_rate:.0f}%)")
                score -= 15
            elif match_rate < 60:
                warnings.append(f"Moderate keyword match ({match_rate:.0f}%) - could be improved")
        
        # File format check
        if '.docx' not in str(resume_text) and '.pdf' not in str(resume_text):
            warnings.append("Ensure you're using .docx or .pdf format (not .doc)")
        
        return {
            'score': max(0, score),
            'grade': 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D',
            'issues': issues,
            'warnings': warnings,
            'matched_keywords': matched_keywords[:10] if job_description else [],
            'missing_keywords': missing_keywords[:10] if job_description else [],
            'recommendations': self._generate_recommendations(issues, warnings, missing_keywords)
        }
    
    def _generate_recommendations(self, issues: List, warnings: List, missing: List) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        if issues:
            recs.append("CRITICAL: Fix all issues listed above before applying")
        
        if missing:
            recs.append(f"Add these keywords if applicable: {', '.join(missing[:5])}")
        
        recs.extend([
            "Use bullet points starting with action verbs",
            "Include quantifiable achievements (increased X by Y%)",
            "Keep to 1-2 pages maximum",
            "Use standard section headings (Experience, Education, Skills)",
            "Save as .pdf or .docx (never .doc)",
            "Use a simple, clean format without tables or graphics",
            "Include keywords from the job description naturally"
        ])
        
        return recs


class CoverLetterGenerator:
    """Generate targeted cover letter templates"""
    
    def generate_template(self, 
                         job_title: str,
                         company: str,
                         your_name: str,
                         key_skills: List[str],
                         why_company: str = "") -> str:
        """
        Generate a cover letter template
        
        Args:
            job_title: Position you're applying for
            company: Company name
            your_name: Your name
            key_skills: 2-3 key skills for this role
            why_company: Why you want to work at this company
            
        Returns:
            Cover letter template
        """
        skills_str = ", ".join(key_skills[:-1]) + f", and {key_skills[-1]}" if len(key_skills) > 1 else key_skills[0]
        
        template = f"""[Your Address]
[City, State ZIP]
[Your Email]
[Your Phone]
[Date]

Hiring Manager
{company}
[Company Address]

Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my background in {skills_str}, I am confident I can contribute meaningfully to your team.

[CUSTOMIZE THIS PARAGRAPH - Specific achievement relevant to the role]
In my previous role, I [specific achievement with numbers/metrics]. This experience has prepared me to [how it relates to new role]. I am particularly drawn to this opportunity because [something specific about the role or company].

{why_company if why_company else "[CUSTOMIZE - Why this company specifically? Reference their mission, recent news, or products]"}

[CUSTOMIZE THIS PARAGRAPH - Another relevant achievement or skill]
Additionally, my experience with [specific skill/project] demonstrates my ability to [relevant outcome]. I believe this aligns well with your need for [requirement from job posting].

I am excited about the possibility of bringing my skills in {skills_str} to {company}. I would welcome the opportunity to discuss how my background and enthusiasm would be a strong fit for your team.

Thank you for considering my application. I look forward to hearing from you.

Sincerely,
{your_name}

[REMEMBER TO CUSTOMIZE EACH SECTION MARKED WITH BRACKETS]
"""
        return template


class ResumeVersionManager:
    """Manage and A/B test different resume versions"""
    
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.versions_file = self.tracking_dir / "resume_versions.json"
        self.versions = self._load_versions()
    
    def _load_versions(self) -> Dict:
        """Load resume version tracking"""
        if not self.versions_file.exists():
            return {
                'versions': [],
                'performance': {}
            }
        
        with open(self.versions_file, 'r') as f:
            return json.load(f)
    
    def _save_versions(self):
        """Save version data"""
        with open(self.versions_file, 'w') as f:
            json.dump(self.versions, f, indent=2)
    
    def add_version(self, version_name: str, description: str, focus: str):
        """
        Track a new resume version
        
        Args:
            version_name: Version identifier (e.g., "tech_v2", "manager_focused")
            description: What's different about this version
            focus: What type of roles this targets
        """
        version = {
            'name': version_name,
            'description': description,
            'focus': focus,
            'created': datetime.now().isoformat(),
            'applications': 0,
            'responses': 0,
            'interviews': 0
        }
        
        self.versions['versions'].append(version)
        self.versions['performance'][version_name] = {
            'applications': 0,
            'responses': 0,
            'interviews': 0,
            'response_rate': 0
        }
        
        self._save_versions()
        print(f"Resume version '{version_name}' added")
    
    def record_result(self, version_name: str, result: str):
        """
        Record result for a resume version
        
        result: 'application', 'response', or 'interview'
        """
        if version_name not in self.versions['performance']:
            print(f"Version '{version_name}' not found")
            return
        
        perf = self.versions['performance'][version_name]
        
        if result == 'application':
            perf['applications'] += 1
        elif result == 'response':
            perf['responses'] += 1
        elif result == 'interview':
            perf['interviews'] += 1
        
        # Recalculate rate
        if perf['applications'] > 0:
            perf['response_rate'] = (perf['responses'] / perf['applications']) * 100
        
        self._save_versions()
    
    def get_best_version(self) -> tuple[str, float]:
        """Get the best performing resume version"""
        best_version = None
        best_rate = 0
