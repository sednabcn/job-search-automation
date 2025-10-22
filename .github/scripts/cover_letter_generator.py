# scripts/cover_letter_generator.py
"""
AI-Powered Cover Letter Generator
Uses GPT-4 to create tailored cover letters
"""

import openai
from pathlib import Path

class CoverLetterGenerator:
    def __init__(self, api_key):
        openai.api_key = api_key
        self.template = self.load_template()
        
    def generate(self, job_posting, cv_content, scoring_data):
        """
        Generate personalized cover letter
        """
        prompt = f"""
        Write a professional cover letter for:
        
        JOB TITLE: {job_posting['title']}
        COMPANY: {job_posting['company']}
        
        KEY REQUIREMENTS:
        {job_posting['requirements']}
        
        MY BACKGROUND:
        {cv_content[:1000]}  # First 1000 chars of CV
        
        MATCHED SKILLS:
        {', '.join(scoring_data['skills_matched'])}
        
        TONE: Professional, enthusiastic, concise (250 words max)
        FOCUS: Match my experience to their specific needs
        STRUCTURE: 3 paragraphs (intro, body with 2-3 examples, closing)
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert career coach writing cover letters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        cover_letter = response.choices[0].message.content
        
        return {
            'content': cover_letter,
            'company': job_posting['company'],
            'position': job_posting['title'],
            'generated_at': datetime.now().isoformat(),
            'model': 'gpt-4'
        }
    
    def save_cover_letter(self, cover_letter_data, job_id):
        """Save to job_search/cover_letters/"""
        output_dir = Path('job_search/cover_letters')
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{job_id}_{cover_letter_data['company'].replace(' ', '_')}.txt"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(cover_letter_data['content'])
        
        return str(filepath)


    Configuration in campaign:
json{
  "name": "ai-powered-applications",
  "generate_cover_letters": true,
  "cover_letter_config": {
    "model": "gpt-4",
    "tone": "professional",
    "max_length": 250,
    "focus_areas": ["technical_skills", "leadership", "achievements"]
  }
}
