#!/usr/bin/env python3
"""
Enhanced AI-Powered Cover Letter Generator
===========================================
Features:
- Multiple AI providers (OpenAI, Anthropic, Local LLMs)
- Template-based generation with customization
- Company research integration
- Tone and style customization
- Quality scoring and validation
- Caching to reduce API costs
- Batch generation support
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import re
import argparse

# Try importing AI libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available. Install: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class CoverLetterGenerator:
    """Enhanced cover letter generator with multiple AI providers and templates"""
    
    # Tone presets
    TONES = {
        'professional': {
            'description': 'Formal and polished',
            'keywords': ['expertise', 'proficiency', 'demonstrated', 'accomplished']
        },
        'enthusiastic': {
            'description': 'Energetic and passionate',
            'keywords': ['excited', 'passionate', 'eager', 'thrilled']
        },
        'confident': {
            'description': 'Assertive and self-assured',
            'keywords': ['proven', 'skilled', 'excel', 'deliver']
        },
        'collaborative': {
            'description': 'Team-focused and cooperative',
            'keywords': ['collaborate', 'team', 'partnership', 'together']
        }
    }
    
    # Industry-specific templates
    INDUSTRY_CONTEXTS = {
        'tech': {
            'focus': 'technical skills, innovation, problem-solving',
            'keywords': ['scalable', 'architecture', 'optimization', 'agile']
        },
        'finance': {
            'focus': 'analytical skills, risk management, regulatory knowledge',
            'keywords': ['analysis', 'compliance', 'strategy', 'metrics']
        },
        'healthcare': {
            'focus': 'patient care, regulatory compliance, compassion',
            'keywords': ['patient-centered', 'quality', 'outcomes', 'safety']
        },
        'startup': {
            'focus': 'versatility, fast-paced environment, ownership',
            'keywords': ['dynamic', 'ownership', 'impact', 'growth']
        }
    }
    
    def __init__(self, 
                 provider: str = 'openai',
                 api_key: Optional[str] = None,
                 cache_dir: str = 'job_search/cover_letters/cache',
                 templates_dir: str = 'cover_letter'):
        """
        Initialize the generator
        
        Args:
            provider: 'openai', 'anthropic', or 'local'
            api_key: API key for the provider
            cache_dir: Directory for caching generated letters
            templates_dir: Directory for custom templates
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir = Path(templates_dir)
        
        # Statistics tracking
        self.stats = {
            'generated': 0,
            'cached': 0,
            'failed': 0,
            'api_calls': 0,
            'total_tokens': 0
        }
        
        # Initialize AI client
        self._init_ai_client()
        
        # Load templates and profile
        self.templates = self._load_templates()
        self.profile = self._load_profile()
    
    def _init_ai_client(self):
        """Initialize the AI provider client"""
        if self.provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI library not installed")
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            openai.api_key = self.api_key
            self.model = 'gpt-4-turbo-preview'
            
        elif self.provider == 'anthropic':
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic library not installed")
            if not self.api_key:
                raise ValueError("Anthropic API key not provided")
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = 'claude-3-5-sonnet-20241022'
            
        elif self.provider == 'local':
            print("⚠️  Using local LLM - ensure Ollama/LMStudio is running")
            self.model = 'mistral'
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _load_templates(self) -> Dict:
        """Load cover letter templates"""
        templates = {
            'default': {
                'structure': [
                    'opening_hook',
                    'background_match',
                    'key_achievements',
                    'company_alignment',
                    'closing_call_to_action'
                ],
                'max_words': 300
            }
        }
        
        # Load custom templates if available
        template_file = self.templates_dir / 'templates.json'
        if template_file.exists():
            with open(template_file) as f:
                custom = json.load(f)
                templates.update(custom)
        
        return templates
    
    def _load_profile(self) -> Dict:
        """Load user profile for personalization"""
        profile_paths = [
            Path('contacts/profile.json'),
            Path('profile.json'),
            Path('cv/profile.json')
        ]
        
        for path in profile_paths:
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        
        return {
            'name': 'Your Name',
            'email': 'your.email@example.com',
            'skills': {'required': [], 'preferred': []},
            'achievements': [],
            'career_goals': ''
        }
    
    def _get_cache_key(self, job: Dict, cv_summary: str, config: Dict) -> str:
        """Generate cache key for a cover letter"""
        # Create hash from job details and config
        cache_data = {
            'job_id': job.get('id', ''),
            'company': job.get('company', ''),
            'title': job.get('title', ''),
            'cv_hash': hashlib.md5(cv_summary.encode()).hexdigest()[:8],
            'config': config
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if cover letter exists in cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file) as f:
                cached = json.load(f)
                
                # Check if cache is recent (within 7 days)
                cache_date = datetime.fromisoformat(cached.get('generated_at', '2020-01-01'))
                age_days = (datetime.now() - cache_date).days
                
                if age_days <= 7:
                    print(f"   ✅ Using cached letter (age: {age_days} days)")
                    self.stats['cached'] += 1
                    return cached
        
        return None
    
    def _save_to_cache(self, cache_key: str, letter_data: Dict):
        """Save generated letter to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(letter_data, f, indent=2)
    
    def _extract_cv_highlights(self, cv_content: str, job: Dict) -> str:
        """Extract relevant CV highlights based on job requirements"""
        # Simple keyword extraction (can be enhanced with NLP)
        job_keywords = set()
        
        # Extract from job title and description
        for field in ['title', 'description', 'requirements']:
            text = job.get(field, '').lower()
            # Extract words (simplified - could use NLP for better extraction)
            words = re.findall(r'\b[a-z]{3,}\b', text)
            job_keywords.update(words)
        
        # Find matching sections in CV
        cv_lines = cv_content.split('\n')
        relevant_lines = []
        
        for line in cv_lines:
            line_lower = line.lower()
            # Check if line contains job-relevant keywords
            if any(keyword in line_lower for keyword in job_keywords):
                relevant_lines.append(line.strip())
        
        # Return top relevant highlights (max 500 chars)
        highlights = '\n'.join(relevant_lines[:10])
        return highlights[:500] if highlights else cv_content[:500]
    
    def _build_prompt(self, 
                     job: Dict, 
                     cv_highlights: str, 
                     config: Dict) -> str:
        """Build the prompt for AI generation"""
        
        tone = config.get('tone', 'professional')
        industry = config.get('industry', 'tech')
        max_words = config.get('max_words', 300)
        focus_areas = config.get('focus_areas', [])
        
        # Get industry context
        industry_info = self.INDUSTRY_CONTEXTS.get(industry, self.INDUSTRY_CONTEXTS['tech'])
        tone_info = self.TONES.get(tone, self.TONES['professional'])
        
        # Build comprehensive prompt
        prompt = f"""Write a compelling cover letter for this job application:

JOB DETAILS:
Company: {job.get('company', 'N/A')}
Position: {job.get('title', 'N/A')}
Location: {job.get('location', 'Remote')}

JOB REQUIREMENTS:
{job.get('requirements', job.get('description', 'N/A'))[:500]}

MY RELEVANT EXPERIENCE:
{cv_highlights}

MATCHED SKILLS:
{', '.join(job.get('skills_matched', []))}

JOB SCORE: {job.get('score', 'N/A')}/100
SCORE REASONS: {'; '.join(job.get('score_reasons', [])[:3])}

WRITING GUIDELINES:
- Tone: {tone} ({tone_info['description']})
- Industry: {industry} (Focus on: {industry_info['focus']})
- Length: Exactly {max_words} words (strictly adhere to this limit)
- Structure: 3 paragraphs
  1. Opening: Hook with specific interest in company/role
  2. Body: 2-3 concrete examples matching job requirements
  3. Closing: Clear call-to-action

FOCUS AREAS: {', '.join(focus_areas) if focus_areas else 'technical skills, achievements, cultural fit'}

REQUIREMENTS:
- Use active voice and strong verbs
- Include specific metrics/achievements where possible
- Demonstrate knowledge of company (if available)
- Show enthusiasm without being overly casual
- Avoid clichés like "team player" or "think outside the box"
- Make it personal and authentic, not generic
- Use keywords from job description naturally

Generate ONLY the cover letter text, no subject line or metadata."""

        return prompt
    
    def _call_ai(self, prompt: str) -> Tuple[str, Dict]:
        """Call AI provider to generate cover letter"""
        self.stats['api_calls'] += 1
        
        try:
            if self.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert career coach and professional writer specializing in compelling cover letters. Write personalized, achievement-focused letters that demonstrate clear value to employers."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )
                
                content = response.choices[0].message.content
                metadata = {
                    'tokens': response.usage.total_tokens,
                    'model': self.model,
                    'finish_reason': response.choices[0].finish_reason
                }
                self.stats['total_tokens'] += response.usage.total_tokens
                
            elif self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    temperature=0.7,
                    system="You are an expert career coach writing compelling, personalized cover letters.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                content = response.content[0].text
                metadata = {
                    'tokens': response.usage.input_tokens + response.usage.output_tokens,
                    'model': self.model,
                    'stop_reason': response.stop_reason
                }
                self.stats['total_tokens'] += metadata['tokens']
                
            else:  # local
                # Placeholder for local LLM integration (Ollama, LMStudio, etc.)
                content = "Local LLM integration - implement with your preferred local model"
                metadata = {'tokens': 0, 'model': 'local'}
            
            return content, metadata
            
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")
    
    def _validate_letter(self, content: str, config: Dict) -> Tuple[bool, List[str]]:
        """Validate generated cover letter quality"""
        issues = []
        
        # Check length
        word_count = len(content.split())
        max_words = config.get('max_words', 300)
        
        if word_count > max_words * 1.2:
            issues.append(f"Too long: {word_count} words (max: {max_words})")
        elif word_count < max_words * 0.6:
            issues.append(f"Too short: {word_count} words (min: {int(max_words * 0.6)})")
        
        # Check for generic phrases (red flags)
        generic_phrases = [
            'i am writing to',
            'i am interested in',
            'perfect fit',
            'team player',
            'think outside the box',
            'hit the ground running',
            'dear sir/madam',
            'to whom it may concern'
        ]
        
        content_lower = content.lower()
        found_generic = [phrase for phrase in generic_phrases if phrase in content_lower]
        
        if found_generic:
            issues.append(f"Generic phrases detected: {', '.join(found_generic[:3])}")
        
        # Check for paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            issues.append("Missing paragraph breaks (should have 3 paragraphs)")
        
        # Check for numbers/metrics (good sign)
        has_numbers = bool(re.search(r'\d+%|\d+x|\d+\+', content))
        if not has_numbers:
            issues.append("Consider adding quantifiable achievements")
        
        # Overall validation
        is_valid = len(issues) == 0 or (len(issues) == 1 and 'consider adding' in issues[0].lower())
        
        return is_valid, issues
    
    def generate(self,
                job: Dict,
                cv_content: str,
                config: Optional[Dict] = None) -> Dict:
        """
        Generate a cover letter for a job posting
        
        Args:
            job: Job posting dictionary
            cv_content: CV/resume text content
            config: Configuration for generation
        
        Returns:
            Dictionary with cover letter and metadata
        """
        config = config or {}
        
        # Set defaults
        config.setdefault('tone', 'professional')
        config.setdefault('industry', 'tech')
        config.setdefault('max_words', 300)
        config.setdefault('focus_areas', ['technical_skills', 'achievements'])
        
        print(f"\n📝 Generating cover letter for: {job.get('company')} - {job.get('title')}")
        print(f"   Tone: {config['tone']} | Industry: {config['industry']} | Max words: {config['max_words']}")
        
        # Check cache first
        cache_key = self._get_cache_key(job, cv_content[:100], config)
        cached = self._check_cache(cache_key)
        
        if cached:
            return cached
        
        # Extract relevant CV highlights
        cv_highlights = self._extract_cv_highlights(cv_content, job)
        
        # Build prompt
        prompt = self._build_prompt(job, cv_highlights, config)
        
        # Generate with AI
        try:
            content, ai_metadata = self._call_ai(prompt)
            
            # Validate
            is_valid, issues = self._validate_letter(content, config)
            
            if not is_valid:
                print(f"   ⚠️  Quality issues detected:")
                for issue in issues:
                    print(f"      - {issue}")
            
            # Build result
            result = {
                'content': content.strip(),
                'company': job.get('company'),
                'position': job.get('title'),
                'job_id': job.get('id'),
                'generated_at': datetime.now().isoformat(),
                'provider': self.provider,
                'model': self.model,
                'config': config,
                'ai_metadata': ai_metadata,
                'validation': {
                    'is_valid': is_valid,
                    'issues': issues
                },
                'word_count': len(content.split()),
                'cache_key': cache_key
            }
            
            # Save to cache
            self._save_to_cache(cache_key, result)
            
            self.stats['generated'] += 1
            print(f"   ✅ Generated ({len(content.split())} words)")
            
            return result
            
        except Exception as e:
            self.stats['failed'] += 1
            print(f"   ❌ Generation failed: {e}")
            raise
    
    def generate_batch(self,
                      jobs: List[Dict],
                      cv_content: str,
                      config: Optional[Dict] = None,
                      max_count: int = 20) -> List[Dict]:
        """
        Generate cover letters for multiple jobs
        
        Args:
            jobs: List of job posting dictionaries
            cv_content: CV/resume text content
            config: Configuration for generation
            max_count: Maximum number to generate
        
        Returns:
            List of cover letter dictionaries
        """
        config = config or {}
        results = []
        
        # Filter high-score jobs
        high_score_jobs = [j for j in jobs if j.get('score', 0) >= 70]
        high_score_jobs = high_score_jobs[:max_count]
        
        print(f"\n{'='*70}")
        print(f"📝 BATCH COVER LETTER GENERATION")
        print(f"{'='*70}")
        print(f"Total jobs: {len(jobs)}")
        print(f"High-score jobs (≥70): {len(high_score_jobs)}")
        print(f"Generating for: {len(high_score_jobs)} jobs")
        print(f"Provider: {self.provider} ({self.model})")
        
        for i, job in enumerate(high_score_jobs, 1):
            print(f"\n[{i}/{len(high_score_jobs)}]", end=" ")
            
            try:
                # Adjust config based on industry if detected
                job_config = config.copy()
                
                # Auto-detect industry from company/description
                description = job.get('description', '').lower()
                if any(word in description for word in ['startup', 'founder', 'seed']):
                    job_config['industry'] = 'startup'
                elif any(word in description for word in ['bank', 'finance', 'trading']):
                    job_config['industry'] = 'finance'
                elif any(word in description for word in ['patient', 'clinical', 'medical']):
                    job_config['industry'] = 'healthcare'
                
                letter = self.generate(job, cv_content, job_config)
                results.append(letter)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        print(f"\n{'='*70}")
        print(f"📊 GENERATION SUMMARY")
        print(f"{'='*70}")
        print(f"Generated: {self.stats['generated']}")
        print(f"Cached: {self.stats['cached']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"API calls: {self.stats['api_calls']}")
        print(f"Total tokens: {self.stats['total_tokens']:,}")
        
        if self.provider == 'openai':
            # Rough cost estimate (GPT-4 Turbo pricing)
            estimated_cost = (self.stats['total_tokens'] / 1000) * 0.01  # $0.01 per 1K tokens
            print(f"Estimated cost: ${estimated_cost:.2f}")
        
        return results
    
    def save_cover_letter(self, 
                         letter_data: Dict, 
                         job_id: str,
                         output_dir: str = 'job_search/cover_letters') -> str:
        """
        Save cover letter to file
        
        Args:
            letter_data: Letter data dictionary
            job_id: Job identifier
            output_dir: Output directory
        
        Returns:
            Path to saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        company = letter_data['company'].replace(' ', '_').replace('/', '-')
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{job_id}_{company}_{timestamp}.txt"
        
        filepath = output_path / filename
        
        # Write cover letter
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Cover Letter for {letter_data['company']}\n")
            f.write(f"Position: {letter_data['position']}\n")
            f.write(f"Generated: {letter_data['generated_at']}\n")
            f.write(f"{'='*70}\n\n")
            f.write(letter_data['content'])
            f.write(f"\n\n{'='*70}\n")
            f.write(f"Word count: {letter_data['word_count']}\n")
            f.write(f"Provider: {letter_data['provider']} ({letter_data['model']})\n")
        
        # Also save metadata as JSON
        metadata_file = output_path / f"{job_id}_{company}_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(letter_data, f, indent=2)
        
        print(f"   💾 Saved to: {filepath}")
        
        return str(filepath)


def main():
    """CLI interface for cover letter generation"""
    parser = argparse.ArgumentParser(description='Generate AI-powered cover letters')
    
    parser.add_argument('--jobs', required=True, help='Path to jobs JSON file')
    parser.add_argument('--cv', required=True, help='Path to CV/resume file')
    parser.add_argument('--profile', default='contacts/profile.json', help='Path to profile JSON')
    parser.add_argument('--output-dir', default='job_search/cover_letters', help='Output directory')
    parser.add_argument('--max-count', type=int, default=20, help='Max cover letters to generate')
    parser.add_argument('--provider', default='openai', choices=['openai', 'anthropic', 'local'], help='AI provider')
    parser.add_argument('--tone', default='professional', choices=list(CoverLetterGenerator.TONES.keys()), help='Writing tone')
    parser.add_argument('--industry', default='tech', choices=list(CoverLetterGenerator.INDUSTRY_CONTEXTS.keys()), help='Industry context')
    parser.add_argument('--max-words', type=int, default=300, help='Maximum words per letter')
    parser.add_argument('--api-key', help='API key (or set via environment variable)')
    
    args = parser.parse_args()
    
    # Load jobs
    with open(args.jobs) as f:
        jobs = json.load(f)
    
    print(f"📄 Loaded {len(jobs)} jobs from {args.jobs}")
    
    # Load CV
    with open(args.cv, encoding='utf-8') as f:
        cv_content = f.read()
    
    print(f"📄 Loaded CV from {args.cv} ({len(cv_content)} chars)")
    
    # Initialize generator
    try:
        generator = CoverLetterGenerator(
            provider=args.provider,
            api_key=args.api_key
        )
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return 1
    
    # Configure generation
    config = {
        'tone': args.tone,
        'industry': args.industry,
        'max_words': args.max_words,
        'focus_areas': ['technical_skills', 'achievements', 'cultural_fit']
    }
    
    # Generate batch
    try:
        results = generator.generate_batch(
            jobs=jobs,
            cv_content=cv_content,
            config=config,
            max_count=args.max_count
        )
        
        # Save all letters
        print(f"\n💾 Saving cover letters...")
        for result in results:
            generator.save_cover_letter(
                result,
                result['job_id'],
                args.output_dir
            )
        
        print(f"\n✅ Successfully generated {len(results)} cover letters!")
        print(f"📁 Saved to: {args.output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Batch generation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
