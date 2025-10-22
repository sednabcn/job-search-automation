# scripts/application_prefiller.py
"""
Application Package Generator
Creates complete application packages with all materials
"""

class ApplicationPrefiller:
    def __init__(self, profile_path='contacts/profile.json'):
        self.profile = self.load_profile(profile_path)
        
    def create_application_package(self, job_posting, cv_path, cover_letter_path):
        """
        Create complete application package
        """
        package_id = f"app_{job_posting['id']}_{datetime.now().strftime('%Y%m%d')}"
        package_dir = Path(f'job_search/application_packages/{package_id}')
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy CV
        shutil.copy(cv_path, package_dir / 'CV.pdf')
        
        # Copy cover letter
        shutil.copy(cover_letter_path, package_dir / 'Cover_Letter.txt')
        
        # Generate application form data
        form_data = {
            'personal_info': {
                'name': self.profile['name'],
                'email': self.profile['email'],
                'phone': self.profile['phone'],
                'location': self.profile['location']
            },
            'job_details': {
                'position': job_posting['title'],
                'company': job_posting['company'],
                'job_url': job_posting['url']
            },
            'questions': self.generate_common_answers(job_posting),
            'salary_expectation': self.calculate_salary_expectation(job_posting)
        }
        
        # Save as JSON for easy copy-paste
        with open(package_dir / 'application_data.json', 'w') as f:
            json.dump(form_data, f, indent=2)
        
        # Create human-readable checklist
        checklist = self.create_application_checklist(job_posting, form_data)
        with open(package_dir / 'APPLICATION_CHECKLIST.md', 'w') as f:
            f.write(checklist)
        
        return package_dir
    
    def generate_common_answers(self, job_posting):
        """Pre-fill common application questions"""
        return {
            'why_this_company': f"Interested in {job_posting['company']}'s work in...",
            'why_this_role': f"Excited about {job_posting['title']} because...",
            'start_date': 'Immediately / 2 weeks notice',
            'work_authorization': self.profile['work_authorization'],
            'sponsorship_needed': self.profile['needs_sponsorship'],
            'salary_expectation': self.profile['salary_range']
        }
```

**Package structure:**
```
job_search/application_packages/
└── app_12345_20241022/
    ├── CV.pdf
    ├── Cover_Letter.txt
    ├── application_data.json
    ├── APPLICATION_CHECKLIST.md
    └── job_details.json
