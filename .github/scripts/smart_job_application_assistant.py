#!/usr/bin/env python3
"""
Smart Job Application Assistant
================================
Intelligent preparation system that assists with job applications
while maintaining human oversight and control.

Philosophy: Prepare everything perfectly, but let humans submit.
"""

import json
import os
import webbrowser
import pyperclip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re


@dataclass
class JobApplication:
    """Represents a job application with all prepared data"""
    job_id: str
    title: str
    company: str
    platform: str
    url: str
    requirements: List[str]
    questions: List[Dict[str, str]]
    deadline: Optional[str]
    salary_range: Optional[str]
    location: str
    work_mode: str
    
    # Prepared data
    selected_cv: str
    cover_letter: str
    answers: Dict[str, str]
    match_score: float
    
    # Metadata
    prepared_at: str
    status: str = "prepared"
    notes: str = ""


class SmartJobAssistant:
    """
    Smart Job Application Assistant
    
    Features:
    - Intelligent CV selection
    - Tailored cover letter generation
    - Pre-filled form data preparation
    - Application tracking and reminders
    - Quality scoring and filtering
    - One-click workflow preparation
    """
    
    def __init__(self, data_dir: str = "job_search"):
        self.data_dir = Path(data_dir)
        self.cv_dir = Path("cv")
        self.cover_letter_dir = Path("cover_letter")
        self.templates_dir = Path("templates")
        
        # Load configurations
        self.personal_info = self._load_personal_info()
        self.cv_versions = self._load_cv_versions()
        self.cover_letter_templates = self._load_templates()
        
        # Tracking files
        self.prepared_apps = self.data_dir / "prepared_applications.json"
        self.submitted_apps = self.data_dir / "submitted_applications.json"
        self.reminders = self.data_dir / "application_reminders.json"
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        for directory in [self.data_dir, self.cv_dir, self.cover_letter_dir, self.templates_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_personal_info(self) -> Dict:
        """Load personal information for applications"""
        info_file = Path("config/personal_info.json")
        
        if info_file.exists():
            with open(info_file, 'r') as f:
                return json.load(f)
        
        # Default template
        return {
            "name": "Your Full Name",
            "email": "your.email@example.com",
            "phone": "+44 XXXX XXXXXX",
            "linkedin": "linkedin.com/in/yourprofile",
            "github": "github.com/yourprofile",
            "portfolio": "yourportfolio.com",
            "location": "London, UK",
            "right_to_work": "Yes",
            "notice_period": "2 weeks",
            "salary_expectations": "Competitive",
            "availability": "Immediate"
        }
    
    def _load_cv_versions(self) -> Dict[str, Dict]:
        """Load different CV versions and their focus areas"""
        cv_config = self.cv_dir / "cv_versions.json"
        
        if cv_config.exists():
            with open(cv_config, 'r') as f:
                return json.load(f)
        
        # Default CV versions
        return {
            "technical": {
                "file": "cv_technical.pdf",
                "focus": ["python", "machine learning", "data science", "AI", "algorithms"],
                "suitable_for": ["Software Engineer", "Data Scientist", "ML Engineer"]
            },
            "leadership": {
                "file": "cv_leadership.pdf",
                "focus": ["team lead", "management", "strategy", "stakeholder", "project"],
                "suitable_for": ["Team Lead", "Manager", "Senior", "Principal"]
            },
            "fullstack": {
                "file": "cv_fullstack.pdf",
                "focus": ["frontend", "backend", "web development", "API", "database"],
                "suitable_for": ["Full Stack", "Web Developer", "Backend", "Frontend"]
            },
            "general": {
                "file": "cv_general.pdf",
                "focus": [],
                "suitable_for": []
            }
        }
    
    def _load_templates(self) -> Dict[str, str]:
        """Load cover letter templates"""
        templates = {}
        template_dir = self.templates_dir / "cover_letters"
        template_dir.mkdir(parents=True, exist_ok=True)
        
        for template_file in template_dir.glob("*.txt"):
            with open(template_file, 'r') as f:
                templates[template_file.stem] = f.read()
        
        # Default template if none exist
        if not templates:
            templates["default"] = self._get_default_cover_letter_template()
        
        return templates
    
    def _get_default_cover_letter_template(self) -> str:
        """Get default cover letter template"""
        return """Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my background in {relevant_skills}, I am excited about the opportunity to contribute to your team.

{why_interested}

Key qualifications that make me an ideal candidate:
{qualifications}

{specific_value_proposition}

I am particularly drawn to {company} because {company_reason}. I believe my {key_strength} would be valuable in achieving {company_goal}.

Thank you for considering my application. I look forward to discussing how I can contribute to {company}'s success.

Best regards,
{your_name}
"""
    
    def calculate_match_score(self, job: Dict) -> float:
        """
        Calculate how well the job matches your profile
        
        Factors:
        - Skills match
        - Experience level fit
        - Location preference
        - Salary range
        - Work mode preference
        """
        score = 0.0
        max_score = 100.0
        
        # Load your skills profile
        your_skills = self._load_your_skills()
        required_skills = job.get('requirements', [])
        
        # Skills match (40 points)
        if required_skills and your_skills:
            matched_skills = sum(1 for skill in required_skills 
                                if any(your_skill.lower() in skill.lower() 
                                      for your_skill in your_skills))
            skills_score = (matched_skills / len(required_skills)) * 40
            score += skills_score
        else:
            score += 20  # Default if no requirements listed
        
        # Experience level (20 points)
        experience_keywords = {
            'junior': 1, 'mid': 2, 'senior': 3, 'lead': 4, 'principal': 5
        }
        job_title = job.get('title', '').lower()
        for keyword, level in experience_keywords.items():
            if keyword in job_title:
                # Assuming you're looking for mid to senior roles
                if level in [2, 3]:
                    score += 20
                elif level in [1, 4]:
                    score += 15
                break
        else:
            score += 10
        
        # Location and work mode (20 points)
        location = job.get('location', '').lower()
        work_mode = job.get('work_mode', '').lower()
        
        if 'remote' in work_mode or 'hybrid' in work_mode:
            score += 10
        if 'london' in location or 'remote' in location:
            score += 10
        
        # Salary (10 points)
        salary = job.get('salary_range', '')
        if salary and ('competitive' in salary.lower() or any(char.isdigit() for char in salary)):
            score += 10
        
        # Company reputation (10 points)
        company_size = job.get('company_size', '')
        if company_size in ['large', 'enterprise', 'startup']:
            score += 10
        
        return min(score, max_score)
    
    def _load_your_skills(self) -> List[str]:
        """Load your skills from profile"""
        skills_file = Path("config/my_skills.json")
        
        if skills_file.exists():
            with open(skills_file, 'r') as f:
                return json.load(f).get('skills', [])
        
        return ["Python", "Machine Learning", "Data Science", "API Development", 
                "SQL", "Git", "Agile", "Problem Solving"]
    
    def select_best_cv(self, job: Dict) -> str:
        """
        Intelligently select the most appropriate CV version
        based on job requirements
        """
        job_title = job.get('title', '').lower()
        requirements = [r.lower() for r in job.get('requirements', [])]
        
        best_match = "general"
        best_score = 0
        
        for cv_name, cv_info in self.cv_versions.items():
            score = 0
            
            # Check if job title matches suitable_for
            for suitable in cv_info.get('suitable_for', []):
                if suitable.lower() in job_title:
                    score += 10
            
            # Check focus keywords in requirements
            for focus_keyword in cv_info.get('focus', []):
                if any(focus_keyword.lower() in req for req in requirements):
                    score += 5
            
            if score > best_score:
                best_score = score
                best_match = cv_name
        
        return cv_info['file']
    
    def generate_cover_letter(self, job: Dict) -> str:
        """
        Generate a tailored cover letter for the job
        """
        template = self.cover_letter_templates.get('default', '')
        
        # Extract key information
        job_title = job.get('title', 'this position')
        company = job.get('company', 'your company')
        requirements = job.get('requirements', [])
        
        # Generate dynamic content
        relevant_skills = ', '.join(requirements[:3]) if requirements else "relevant technologies"
        
        # Create qualifications list
        qualifications_list = []
        for i, req in enumerate(requirements[:4], 1):
            qualifications_list.append(f"{i}. {req}")
        qualifications = '\n'.join(qualifications_list) if qualifications_list else "Strong technical background"
        
        # Fill in template
        cover_letter = template.format(
            job_title=job_title,
            company=company,
            relevant_skills=relevant_skills,
            why_interested=f"I am particularly excited about this opportunity as it aligns perfectly with my experience in {relevant_skills}.",
            qualifications=qualifications,
            specific_value_proposition=f"My experience with {requirements[0] if requirements else 'modern technologies'} has prepared me to make immediate contributions to your team.",
            company_reason="of your innovative approach and strong market position",
            key_strength="technical expertise and collaborative approach",
            company_goal="your technical objectives",
            your_name=self.personal_info.get('name', 'Your Name')
        )
        
        return cover_letter
    
    def generate_application_answers(self, questions: List[Dict]) -> Dict[str, str]:
        """
        Generate intelligent answers to common application questions
        """
        answers = {}
        
        common_answers = {
            'right_to_work': self.personal_info.get('right_to_work', 'Yes'),
            'notice_period': self.personal_info.get('notice_period', '2 weeks'),
            'salary': self.personal_info.get('salary_expectations', 'Competitive'),
            'location': self.personal_info.get('location', 'London, UK'),
            'availability': self.personal_info.get('availability', 'Immediate')
        }
        
        for question in questions:
            q_text = question.get('question', '').lower()
            
            # Match question types
            if 'right to work' in q_text or 'visa' in q_text:
                answers[question['id']] = common_answers['right_to_work']
            elif 'notice period' in q_text:
                answers[question['id']] = common_answers['notice_period']
            elif 'salary' in q_text or 'compensation' in q_text:
                answers[question['id']] = common_answers['salary']
            elif 'location' in q_text or 'based' in q_text:
                answers[question['id']] = common_answers['location']
            elif 'available' in q_text or 'start date' in q_text:
                answers[question['id']] = common_answers['availability']
            else:
                answers[question['id']] = "Please see my CV for details"
        
        return answers
    
    def prepare_application(self, job: Dict) -> JobApplication:
        """
        Prepare a complete job application with all materials
        """
        print(f"\n📋 Preparing application for: {job.get('title')} at {job.get('company')}")
        
        # Calculate match score
        match_score = self.calculate_match_score(job)
        print(f"   Match Score: {match_score:.1f}%")
        
        # Select best CV
        selected_cv = self.select_best_cv(job)
        print(f"   Selected CV: {selected_cv}")
        
        # Generate cover letter
        cover_letter = self.generate_cover_letter(job)
        print(f"   Generated cover letter ({len(cover_letter)} chars)")
        
        # Generate answers to questions
        questions = job.get('questions', [])
        answers = self.generate_application_answers(questions)
        print(f"   Prepared answers for {len(answers)} questions")
        
        # Create application object
        application = JobApplication(
            job_id=job.get('id', f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            title=job.get('title', ''),
            company=job.get('company', ''),
            platform=job.get('platform', 'Unknown'),
            url=job.get('url', ''),
            requirements=job.get('requirements', []),
            questions=questions,
            deadline=job.get('deadline'),
            salary_range=job.get('salary_range'),
            location=job.get('location', ''),
            work_mode=job.get('work_mode', ''),
            selected_cv=selected_cv,
            cover_letter=cover_letter,
            answers=answers,
            match_score=match_score,
            prepared_at=datetime.now().isoformat(),
            status="prepared"
        )
        
        # Save prepared application
        self._save_prepared_application(application)
        
        print(f"   ✅ Application prepared and saved!")
        return application
    
    def _save_prepared_application(self, application: JobApplication):
        """Save prepared application to tracking file"""
        applications = []
        
        if self.prepared_apps.exists():
            with open(self.prepared_apps, 'r') as f:
                applications = json.load(f)
        
        applications.append(asdict(application))
        
        with open(self.prepared_apps, 'w') as f:
            json.dump(applications, f, indent=2)
    
    def create_quick_apply_package(self, application: JobApplication) -> Dict:
        """
        Create a quick-apply package with all necessary data
        """
        package = {
            'personal_info': self.personal_info,
            'job_details': {
                'title': application.title,
                'company': application.company,
                'url': application.url
            },
            'materials': {
                'cv_path': str(self.cv_dir / application.selected_cv),
                'cover_letter': application.cover_letter
            },
            'form_data': application.answers,
            'instructions': [
                "1. Open the job application page (browser will open automatically)",
                "2. Form data has been copied to clipboard",
                "3. Review the pre-filled cover letter",
                "4. Upload the selected CV from the provided path",
                "5. Review everything and click Submit",
                "6. Mark as submitted using: mark_submitted(job_id)"
            ]
        }
        
        return package
    
    def open_application_workflow(self, job_id: str):
        """
        Open a one-click workflow to submit the application
        """
        # Load prepared application
        applications = []
        if self.prepared_apps.exists():
            with open(self.prepared_apps, 'r') as f:
                applications = json.load(f)
        
        application = next((app for app in applications if app['job_id'] == job_id), None)
        
        if not application:
            print(f"❌ No prepared application found for job_id: {job_id}")
            return
        
        print(f"\n🚀 Opening workflow for: {application['title']} at {application['company']}")
        
        # Create quick apply package
        package = self.create_quick_apply_package(
            JobApplication(**application)
        )
        
        # Copy form data to clipboard
        clipboard_data = json.dumps(package['form_data'], indent=2)
        try:
            pyperclip.copy(clipboard_data)
            print("   ✅ Form data copied to clipboard")
        except:
            print("   ⚠️ Could not copy to clipboard. Install pyperclip: pip install pyperclip")
        
        # Save package to temp file
        temp_file = self.data_dir / f"apply_{job_id}.json"
        with open(temp_file, 'w') as f:
            json.dump(package, f, indent=2)
        print(f"   📄 Application package saved to: {temp_file}")
        
        # Display cover letter
        print("\n" + "="*80)
        print("COVER LETTER")
        print("="*80)
        print(application['cover_letter'])
        print("="*80)
        
        # Open job URL in browser
        if application['url']:
            print(f"\n   🌐 Opening job page in browser...")
            webbrowser.open(application['url'])
        
        # Display instructions
        print("\n" + "="*80)
        print("QUICK APPLY INSTRUCTIONS")
        print("="*80)
        for instruction in package['instructions']:
            print(instruction)
        print("="*80)
        
        print(f"\n   💡 CV Location: {package['materials']['cv_path']}")
        print(f"   💾 Full package: {temp_file}")
    
    def mark_submitted(self, job_id: str, notes: str = ""):
        """
        Mark an application as submitted
        """
        # Load prepared applications
        prepared = []
        if self.prepared_apps.exists():
            with open(self.prepared_apps, 'r') as f:
                prepared = json.load(f)
        
        # Find and remove from prepared
        application = None
        prepared_updated = []
        for app in prepared:
            if app['job_id'] == job_id:
                application = app
                application['status'] = 'submitted'
                application['submitted_at'] = datetime.now().isoformat()
                application['notes'] = notes
            else:
                prepared_updated.append(app)
        
        if not application:
            print(f"❌ No prepared application found for job_id: {job_id}")
            return
        
        # Save updated prepared list
        with open(self.prepared_apps, 'w') as f:
            json.dump(prepared_updated, f, indent=2)
        
        # Add to submitted list
        submitted = []
        if self.submitted_apps.exists():
            with open(self.submitted_apps, 'r') as f:
                submitted = json.load(f)
        
        submitted.append(application)
        
        with open(self.submitted_apps, 'w') as f:
            json.dump(submitted, f, indent=2)
        
        print(f"✅ Marked as submitted: {application['title']} at {application['company']}")
        
        # Set reminder for follow-up
        self._create_followup_reminder(application)
    
    def _create_followup_reminder(self, application: Dict):
        """Create a follow-up reminder for 1-2 weeks after submission"""
        reminders = []
        if self.reminders.exists():
            with open(self.reminders, 'r') as f:
                reminders = json.load(f)
        
        followup_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        reminder = {
            'job_id': application['job_id'],
            'title': application['title'],
            'company': application['company'],
            'type': 'follow_up',
            'date': followup_date,
            'message': f"Follow up on application to {application['title']} at {application['company']}",
            'created_at': datetime.now().isoformat()
        }
        
        reminders.append(reminder)
        
        with open(self.reminders, 'w') as f:
            json.dump(reminders, f, indent=2)
        
        print(f"   📅 Follow-up reminder set for: {followup_date[:10]}")
    
    def show_statistics(self):
        """Display application statistics"""
        # Load data
        prepared = []
        submitted = []
        
        if self.prepared_apps.exists():
            with open(self.prepared_apps, 'r') as f:
                prepared = json.load(f)
        
        if self.submitted_apps.exists():
            with open(self.submitted_apps, 'r') as f:
                submitted = json.load(f)
        
        print("\n" + "="*80)
        print("📊 APPLICATION STATISTICS")
        print("="*80)
        print(f"\n📋 Prepared Applications: {len(prepared)}")
        print(f"✅ Submitted Applications: {len(submitted)}")
        
        if prepared:
            avg_score = sum(app.get('match_score', 0) for app in prepared) / len(prepared)
            print(f"📈 Average Match Score (Prepared): {avg_score:.1f}%")
        
        if submitted:
            print(f"\n🗓️  Submission Rate: {len(submitted)} applications")
            
            # Group by platform
            platforms = {}
            for app in submitted:
                platform = app.get('platform', 'Unknown')
                platforms[platform] = platforms.get(platform, 0) + 1
            
            print("\n📍 By Platform:")
            for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
                print(f"   {platform}: {count}")
        
        print("="*80)
    
    def check_reminders(self):
        """Check and display due reminders"""
        if not self.reminders.exists():
            print("📅 No reminders set")
            return
        
        with open(self.reminders, 'r') as f:
            reminders = json.load(f)
        
        now = datetime.now()
        due_reminders = []
        
        for reminder in reminders:
            reminder_date = datetime.fromisoformat(reminder['date'])
            if reminder_date <= now:
                due_reminders.append(reminder)
        
        if not due_reminders:
            print("📅 No due reminders")
            return
        
        print(f"\n🔔 {len(due_reminders)} Due Reminder(s)")
        print("="*80)
        
        for reminder in due_reminders:
            print(f"\n📌 {reminder['message']}")
            print(f"   Company: {reminder['company']}")
            print(f"   Due: {reminder['date'][:10]}")
        
        print("="*80)
    
    def filter_jobs_by_quality(self, jobs: List[Dict], min_score: float = 70.0) -> List[Dict]:
        """
        Filter jobs by quality score
        Quality over quantity approach
        """
        quality_jobs = []
        
        for job in jobs:
            score = self.calculate_match_score(job)
            if score >= min_score:
                job['match_score'] = score
                quality_jobs.append(job)
        
        # Sort by score
        quality_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        print(f"\n🎯 Quality Filter: {len(quality_jobs)}/{len(jobs)} jobs passed (>= {min_score}%)")
        
        return quality_jobs


def main():
    """
    Example usage of Smart Job Assistant
    """
    assistant = SmartJobAssistant()
    
    # Example: Prepare application for a job
    example_job = {
        'id': 'job_12345',
        'title': 'Senior Python Developer',
        'company': 'Tech Corp',
        'url': 'https://example.com/jobs/12345',
        'platform': 'LinkedIn',
        'requirements': ['Python', 'Django', 'REST API', 'PostgreSQL', 'Docker'],
        'questions': [
            {'id': 'q1', 'question': 'Do you have the right to work in the UK?'},
            {'id': 'q2', 'question': 'What is your notice period?'},
            {'id': 'q3', 'question': 'What are your salary expectations?'}
        ],
        'location': 'London, UK',
        'work_mode': 'Hybrid',
        'salary_range': '£70,000 - £90,000',
        'deadline': '2025-11-30'
    }
    
    # Prepare the application
    application = assistant.prepare_application(example_job)
    
    # Open workflow for submission
    # assistant.open_application_workflow(application.job_id)
    
    # After submitting manually, mark as submitted
    # assistant.mark_submitted(application.job_id, notes="Applied via LinkedIn Easy Apply")
    
    # Check statistics
    assistant.show_statistics()
    
    # Check reminders
    assistant.check_reminders()


if __name__ == "__main__":
    main()
