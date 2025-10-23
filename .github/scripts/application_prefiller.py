# scripts/application_prefiller.py
"""
Enhanced Application Package Generator
Creates complete, platform-specific application packages with intelligent pre-filling
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re


class ApplicationPrefiller:
    def __init__(self, profile_path='contacts/profile.json'):
        self.profile = self.load_profile(profile_path)
        self.package_root = Path('job_search/application_packages')
        self.package_root.mkdir(parents=True, exist_ok=True)
        
    def load_profile(self, profile_path: str) -> Dict:
        """Load user profile with validation"""
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            
            # Ensure required fields exist
            required_fields = ['name', 'email', 'phone', 'location']
            for field in required_fields:
                if field not in profile:
                    raise ValueError(f"Missing required field: {field}")
            
            return profile
        except FileNotFoundError:
            print(f"⚠️ Profile not found at {profile_path}, using defaults")
            return self._get_default_profile()
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON in profile, using defaults")
            return self._get_default_profile()
    
    def _get_default_profile(self) -> Dict:
        """Return default profile structure"""
        return {
            'name': 'YOUR_NAME',
            'email': 'your.email@example.com',
            'phone': '+44 XXXX XXXXXX',
            'location': 'London, UK',
            'work_authorization': 'Authorized to work in UK',
            'needs_sponsorship': False,
            'salary_range': '£50,000 - £70,000',
            'notice_period': '2 weeks',
            'linkedin_url': '',
            'portfolio_url': '',
            'github_url': ''
        }
    
    def create_application_package(
        self, 
        job_posting: Dict, 
        cv_path: str, 
        cover_letter_path: Optional[str] = None,
        platform: str = 'generic'
    ) -> Path:
        """
        Create complete application package with platform-specific formatting
        
        Args:
            job_posting: Job details dictionary
            cv_path: Path to CV file
            cover_letter_path: Optional path to cover letter
            platform: Platform name (linkedin, indeed, reed, glassdoor, generic)
        
        Returns:
            Path to created package directory
        """
        # Generate unique package ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        job_id = job_posting.get('id', 'unknown')
        company = self._sanitize_filename(job_posting.get('company', 'company'))
        
        package_id = f"{platform}_{company}_{job_id}_{timestamp}"
        package_dir = self.package_root / package_id
        package_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📦 Creating application package: {package_id}")
        
        # Copy documents
        self._copy_cv(cv_path, package_dir)
        if cover_letter_path:
            self._copy_cover_letter(cover_letter_path, package_dir)
        
        # Generate platform-specific form data
        form_data = self._generate_form_data(job_posting, platform)
        
        # Save structured data
        self._save_json(package_dir / 'application_data.json', form_data)
        self._save_json(package_dir / 'job_details.json', job_posting)
        
        # Create platform-specific checklist
        checklist = self._create_checklist(job_posting, form_data, platform)
        self._save_text(package_dir / 'APPLICATION_CHECKLIST.md', checklist)
        
        # Create quick-copy text file for easy form filling
        quick_copy = self._create_quick_copy_text(form_data)
        self._save_text(package_dir / 'QUICK_COPY.txt', quick_copy)
        
        # Generate platform-specific instructions
        instructions = self._create_platform_instructions(platform, job_posting)
        self._save_text(package_dir / 'PLATFORM_INSTRUCTIONS.md', instructions)
        
        # Create metadata file
        metadata = {
            'package_id': package_id,
            'created_at': datetime.now().isoformat(),
            'platform': platform,
            'job_id': job_id,
            'company': job_posting.get('company'),
            'position': job_posting.get('title'),
            'status': 'prepared',
            'application_url': job_posting.get('url', '')
        }
        self._save_json(package_dir / 'metadata.json', metadata)
        
        print(f"✅ Package created successfully at: {package_dir}")
        return package_dir
    
    def _generate_form_data(self, job_posting: Dict, platform: str) -> Dict:
        """Generate comprehensive form data with platform-specific fields"""
        
        # Base personal information
        form_data = {
            'personal_info': {
                'full_name': self.profile['name'],
                'email': self.profile['email'],
                'phone': self.profile['phone'],
                'location': self.profile['location'],
                'linkedin_url': self.profile.get('linkedin_url', ''),
                'portfolio_url': self.profile.get('portfolio_url', ''),
                'github_url': self.profile.get('github_url', '')
            },
            
            'job_details': {
                'position': job_posting.get('title', ''),
                'company': job_posting.get('company', ''),
                'job_url': job_posting.get('url', ''),
                'job_id': job_posting.get('id', ''),
                'location': job_posting.get('location', ''),
                'salary': job_posting.get('salary', 'Negotiable')
            },
            
            'common_questions': self._generate_common_answers(job_posting),
            
            'availability': {
                'start_date': self.profile.get('notice_period', '2 weeks notice'),
                'work_authorization': self.profile.get('work_authorization', 'Yes'),
                'sponsorship_needed': self.profile.get('needs_sponsorship', False),
                'willing_to_relocate': self._determine_relocation(job_posting)
            },
            
            'compensation': {
                'salary_expectation': self._calculate_salary_expectation(job_posting),
                'salary_range': self.profile.get('salary_range', 'Market rate'),
                'negotiable': True
            }
        }
        
        # Add platform-specific fields
        platform_fields = self._get_platform_specific_fields(platform, job_posting)
        form_data['platform_specific'] = platform_fields
        
        return form_data
    
    def _generate_common_answers(self, job_posting: Dict) -> Dict:
        """Generate smart answers to common application questions"""
        company = job_posting.get('company', 'this company')
        position = job_posting.get('title', 'this role')
        
        return {
            'why_this_company': f"I'm excited about {company}'s innovative approach and strong reputation in the industry. The company's commitment to [specific value from job posting] aligns perfectly with my professional values.",
            
            'why_this_role': f"The {position} position represents an excellent opportunity to leverage my skills in [relevant skills]. I'm particularly drawn to [specific responsibility from job description].",
            
            'key_strengths': "Strong technical skills, proven track record in [domain], excellent communication abilities, and passion for continuous learning.",
            
            'relevant_experience': "I have [X years] of experience in [relevant field], with specific expertise in [key technologies/methods mentioned in job posting].",
            
            'career_goals': "I aim to grow into [senior role] while contributing significantly to innovative projects that make a real impact.",
            
            'availability': self.profile.get('notice_period', 'Immediately / 2 weeks notice'),
            
            'questions_for_employer': [
                "What does success look like in this role after 6 months?",
                "How does the team approach professional development?",
                "What are the biggest challenges the team is currently facing?"
            ]
        }
    
    def _get_platform_specific_fields(self, platform: str, job_posting: Dict) -> Dict:
        """Get platform-specific form fields"""
        
        platform_fields = {
            'linkedin': {
                'easy_apply': job_posting.get('easy_apply', False),
                'connection_request': True,
                'follow_company': True,
                'message_to_recruiter': "I'm very interested in this opportunity and believe my experience aligns well with the role requirements."
            },
            
            'indeed': {
                'resume_upload': True,
                'cover_letter_required': job_posting.get('cover_letter_required', False),
                'assessment_required': job_posting.get('assessment_required', False),
                'employer_questions': job_posting.get('screening_questions', [])
            },
            
            'reed': {
                'cv_upload': True,
                'covering_letter': True,
                'consultancy_name': job_posting.get('agency', 'Direct employer'),
                'send_similar_jobs': True
            },
            
            'glassdoor': {
                'company_rating': job_posting.get('rating', 'N/A'),
                'salary_estimate': job_posting.get('salary_estimate', ''),
                'anonymous_application': False,
                'company_reviews_read': True
            }
        }
        
        return platform_fields.get(platform, {})
    
    def _calculate_salary_expectation(self, job_posting: Dict) -> str:
        """Calculate appropriate salary expectation based on job details"""
        posted_salary = job_posting.get('salary', '')
        profile_range = self.profile.get('salary_range', '')
        
        if posted_salary and posted_salary != 'Not specified':
            return f"Within posted range: {posted_salary}"
        elif profile_range:
            return profile_range
        else:
            return "Competitive market rate based on experience"
    
    def _determine_relocation(self, job_posting: Dict) -> bool:
        """Determine if relocation is needed"""
        job_location = job_posting.get('location', '').lower()
        current_location = self.profile.get('location', '').lower()
        
        # Check for remote
        if 'remote' in job_location or 'hybrid' in job_location:
            return False
        
        # Simple location comparison
        return job_location not in current_location
    
    def _create_checklist(self, job_posting: Dict, form_data: Dict, platform: str) -> str:
        """Create comprehensive application checklist"""
        
        checklist = f"""# Application Checklist
## {job_posting.get('title', 'Position')} at {job_posting.get('company', 'Company')}

**Platform:** {platform.upper()}  
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Application URL:** {job_posting.get('url', 'N/A')}

---

## Pre-Application Tasks

- [ ] Review job description thoroughly
- [ ] Research company on Glassdoor
- [ ] Check LinkedIn for connections at company
- [ ] Tailor CV to highlight relevant experience
- [ ] Prepare cover letter (if required)
- [ ] Review salary expectations
- [ ] Prepare questions for employer

## Application Submission

### Personal Information
- [ ] Full name: `{form_data['personal_info']['full_name']}`
- [ ] Email: `{form_data['personal_info']['email']}`
- [ ] Phone: `{form_data['personal_info']['phone']}`
- [ ] Location: `{form_data['personal_info']['location']}`
- [ ] LinkedIn: `{form_data['personal_info']['linkedin_url']}`

### Documents
- [ ] Upload CV/Resume (file: `CV.pdf`)
- [ ] Upload Cover Letter (file: `Cover_Letter.txt`)
- [ ] Check document formatting

### Key Questions
- [ ] Why this company? *(See QUICK_COPY.txt)*
- [ ] Why this role? *(See QUICK_COPY.txt)*
- [ ] Salary expectation: `{form_data['compensation']['salary_expectation']}`
- [ ] Start date: `{form_data['availability']['start_date']}`
- [ ] Work authorization: `{form_data['availability']['work_authorization']}`
- [ ] Sponsorship needed: `{form_data['availability']['sponsorship_needed']}`

### Platform-Specific
"""
        
        # Add platform-specific checklist items
        if platform == 'linkedin':
            checklist += """
- [ ] Enable Easy Apply if available
- [ ] Send connection request to recruiter
- [ ] Follow company page
- [ ] Add personalized message
"""
        elif platform == 'indeed':
            checklist += """
- [ ] Complete Indeed profile
- [ ] Answer screening questions
- [ ] Complete assessment (if required)
- [ ] Set up job alerts for similar roles
"""
        elif platform == 'reed':
            checklist += """
- [ ] Upload CV to Reed profile
- [ ] Add covering letter
- [ ] Note consultancy/agency name
- [ ] Opt-in for similar job alerts
"""
        elif platform == 'glassdoor':
            checklist += """
- [ ] Read company reviews
- [ ] Check salary estimates
- [ ] Review interview questions
- [ ] Research company culture
"""
        
        checklist += """
## Post-Application Tasks

- [ ] Save confirmation email/number
- [ ] Add to application tracker
- [ ] Set reminder for follow-up (7 days)
- [ ] Connect with recruiter on LinkedIn
- [ ] Research interview questions
- [ ] Prepare for potential interview

## Follow-Up Schedule

- **Day 3:** Check application status
- **Day 7:** Send follow-up email if no response
- **Day 14:** Final follow-up or move to next opportunity

---

**Notes:**
- Keep all confirmation emails
- Document any communication
- Update application tracker immediately
"""
        
        return checklist
    
    def _create_quick_copy_text(self, form_data: Dict) -> str:
        """Create quick-copy text for easy form filling"""
        
        text = f"""# QUICK COPY - Easy Form Filling
## Copy and paste these answers directly into application forms

========================================
PERSONAL INFORMATION
========================================

Full Name: {form_data['personal_info']['full_name']}

Email: {form_data['personal_info']['email']}

Phone: {form_data['personal_info']['phone']}

Location: {form_data['personal_info']['location']}

LinkedIn: {form_data['personal_info']['linkedin_url']}

Portfolio: {form_data['personal_info']['portfolio_url']}

GitHub: {form_data['personal_info']['github_url']}

========================================
COMMON QUESTIONS
========================================

Why are you interested in this company?
---
{form_data['common_questions']['why_this_company']}

Why are you interested in this role?
---
{form_data['common_questions']['why_this_role']}

What are your key strengths?
---
{form_data['common_questions']['key_strengths']}

Describe your relevant experience:
---
{form_data['common_questions']['relevant_experience']}

What are your career goals?
---
{form_data['common_questions']['career_goals']}

========================================
AVAILABILITY & AUTHORIZATION
========================================

Start Date: {form_data['availability']['start_date']}

Work Authorization: {form_data['availability']['work_authorization']}

Sponsorship Required: {form_data['availability']['sponsorship_needed']}

Willing to Relocate: {form_data['availability']['willing_to_relocate']}

========================================
COMPENSATION
========================================

Salary Expectation: {form_data['compensation']['salary_expectation']}

Salary Range: {form_data['compensation']['salary_range']}

Negotiable: {form_data['compensation']['negotiable']}

========================================
QUESTIONS FOR EMPLOYER
========================================

"""
        for i, q in enumerate(form_data['common_questions']['questions_for_employer'], 1):
            text += f"{i}. {q}\n"
        
        text += "\n========================================\n"
        text += "TIP: Keep this file open while filling forms!\n"
        text += "========================================\n"
        
        return text
    
    def _create_platform_instructions(self, platform: str, job_posting: Dict) -> str:
        """Create platform-specific application instructions"""
        
        instructions = {
            'linkedin': f"""# LinkedIn Application Instructions

## Step-by-Step Process

1. **Navigate to Job Posting**
   - URL: {job_posting.get('url', 'N/A')}
   - Ensure you're logged into LinkedIn

2. **Check Easy Apply Eligibility**
   - Look for "Easy Apply" button
   - If not available, click "Apply" for external application

3. **Complete Application**
   - Upload CV from this package
   - Fill required fields (use QUICK_COPY.txt)
   - Answer screening questions if present

4. **Add Personal Touch**
   - Send connection request to recruiter/hiring manager
   - Add personalized message mentioning the role
   - Follow company page

5. **Post-Application**
   - Save confirmation
   - Set up job alert for similar roles
   - Check "Jobs Applied" section regularly

## Tips
- Apply within 24 hours of job posting for best visibility
- Customize connection message to mention specific role
- Engage with company content before/after applying
""",

            'indeed': f"""# Indeed Application Instructions

## Step-by-Step Process

1. **Access Job Posting**
   - URL: {job_posting.get('url', 'N/A')}
   - Log into Indeed account

2. **Prepare Application**
   - Update Indeed CV/Resume
   - Have documents ready from this package

3. **Complete Application Form**
   - Upload CV.pdf
   - Fill employer screening questions
   - Use answers from QUICK_COPY.txt

4. **Assessments**
   - Complete any required Indeed assessments
   - Take seriously - visible to employers

5. **Submit & Track**
   - Review all information
   - Click "Submit Application"
   - Check "My Jobs" for status updates

## Tips
- Complete Indeed profile 100% for better visibility
- Indeed assessments boost application quality
- Set up email alerts for responses
- Check spam folder for employer messages
""",

            'reed': f"""# Reed Application Instructions

## Step-by-Step Process

1. **Navigate to Listing**
   - URL: {job_posting.get('url', 'N/A')}
   - Log into Reed account

2. **Check Agency vs Direct**
   - Note if agency or direct employer
   - Agency: {job_posting.get('agency', 'Unknown')}

3. **Prepare Documents**
   - CV from this package
   - Covering letter if required

4. **Fill Application**
   - Upload CV
   - Add covering letter in text box
   - Complete all required fields

5. **Additional Options**
   - Opt-in for similar job alerts
   - Register with recruitment agency if applicable

## Tips
- Reed often uses recruitment agencies
- Personalize covering letter for each application
- Check agency reviews on Glassdoor
- Follow up with agency directly after 3 days
""",

            'glassdoor': f"""# Glassdoor Application Instructions

## Step-by-Step Process

1. **Research First**
   - Read company reviews
   - Check salary estimates
   - Review interview questions
   - Understand company culture

2. **Access Job Posting**
   - URL: {job_posting.get('url', 'N/A')}
   - May redirect to company website

3. **Complete Application**
   - Usually redirects to external site
   - Have documents ready
   - Use researched information in answers

4. **Leverage Glassdoor Data**
   - Reference company values in application
   - Mention salary research in negotiations
   - Prepare using interview questions

## Tips
- Glassdoor primarily for research
- Application often on external site
- Use insights in cover letter
- Review salary data before stating expectations
""",

            'generic': f"""# Application Instructions

## General Process

1. **Navigate to Job Posting**
   - URL: {job_posting.get('url', 'N/A')}

2. **Prepare Application**
   - Have CV.pdf ready
   - Review QUICK_COPY.txt
   - Prepare cover letter if needed

3. **Fill Application Form**
   - Use information from this package
   - Answer questions thoughtfully
   - Double-check all fields

4. **Submit & Track**
   - Save confirmation
   - Update application tracker
   - Set follow-up reminder

## Tips
- Customize for each application
- Proofread everything
- Follow up after 7 days if no response
"""
        }
        
        return instructions.get(platform, instructions['generic'])
    
    def _copy_cv(self, cv_path: str, package_dir: Path):
        """Copy CV to package directory"""
        cv_source = Path(cv_path)
        if cv_source.exists():
            shutil.copy(cv_source, package_dir / 'CV.pdf')
            print(f"  ✅ CV copied")
        else:
            print(f"  ⚠️ CV not found at {cv_path}")
    
    def _copy_cover_letter(self, cover_letter_path: str, package_dir: Path):
        """Copy cover letter to package directory"""
        cl_source = Path(cover_letter_path)
        if cl_source.exists():
            shutil.copy(cl_source, package_dir / 'Cover_Letter.txt')
            print(f"  ✅ Cover letter copied")
        else:
            print(f"  ⚠️ Cover letter not found at {cover_letter_path}")
    
    def _save_json(self, filepath: Path, data: Dict):
        """Save data as formatted JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_text(self, filepath: Path, content: str):
        """Save text content"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use in filename"""
        # Remove/replace invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = re.sub(r'\s+', '_', name)
        return name[:50]  # Limit length


def main():
    """Example usage"""
    prefiller = ApplicationPrefiller()
    
    # Example job posting
    job = {
        'id': 'job_12345',
        'title': 'Senior Software Engineer',
        'company': 'Tech Corp',
        'location': 'London, UK',
        'salary': '£60,000 - £80,000',
        'url': 'https://example.com/jobs/12345',
        'easy_apply': True
    }
    
    package_dir = prefiller.create_application_package(
        job_posting=job,
        cv_path='cv/my_cv.pdf',
        cover_letter_path='cover_letter/my_cover.txt',
        platform='linkedin'
    )
    
    print(f"\n📦 Package created at: {package_dir}")


if __name__ == '__main__':
    main()

