#!/usr/bin/env python3
"""
CV vs Job Offer Matcher & Scorer
Analyzes CV against job descriptions and provides actionable recommendations
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import difflib

class CVJobMatcher:
    def __init__(self, data_dir: str = "job_search"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Scoring thresholds
        self.THRESHOLDS = {
            "apply_now": 75,        # 75%+ = Strong match, apply immediately
            "apply_caution": 60,    # 60-74% = Apply with some gaps
            "upskill_first": 40,    # 40-59% = Upskill first, then apply
            "not_ready": 0          # <40% = Not ready, significant gaps
        }
        
        # Weight distribution (must sum to 1.0)
        self.WEIGHTS = {
            "required_skills": 0.35,
            "preferred_skills": 0.15,
            "experience": 0.20,
            "education": 0.10,
            "certifications": 0.05,
            "keywords": 0.15
        }
        
        # Skills database
        self.SKILL_CATEGORIES = {
            "programming_languages": [
                "python", "java", "javascript", "typescript", "c++", "c#", "go", 
                "rust", "scala", "r", "julia", "matlab", "sql", "bash", "shell"
            ],
            "ml_frameworks": [
                "pytorch", "tensorflow", "keras", "scikit-learn", "xgboost", 
                "lightgbm", "catboost", "hugging face", "transformers", "jax"
            ],
            "data_tools": [
                "pandas", "numpy", "scipy", "spark", "hadoop", "kafka", 
                "airflow", "dbt", "snowflake", "databricks", "redshift"
            ],
            "cloud_platforms": [
                "aws", "azure", "gcp", "google cloud", "amazon web services",
                "s3", "ec2", "lambda", "sagemaker", "vertex ai"
            ],
            "devops_mlops": [
                "docker", "kubernetes", "mlflow", "wandb", "kubeflow",
                "jenkins", "github actions", "terraform", "ansible"
            ],
            "finance_quant": [
                "quantitative finance", "derivatives", "risk management",
                "portfolio optimization", "algorithmic trading", "hft",
                "market making", "options", "fixed income"
            ],
            "databases": [
                "postgresql", "mysql", "mongodb", "redis", "cassandra",
                "dynamodb", "elasticsearch", "vector databases"
            ],
            "visualization": [
                "tableau", "power bi", "matplotlib", "seaborn", "plotly",
                "d3.js", "grafana"
            ]
        }
        
        # Results file
        self.results_file = self.data_dir / "cv_job_matches.json"
        self.matches = self._load_json(self.results_file, [])
    
    def _load_json(self, filepath: Path, default):
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, filepath: Path, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def parse_cv(self, cv_text: str) -> Dict:
        """Extract structured information from CV text"""
        cv_data = {
            "skills": self._extract_skills(cv_text),
            "experience_years": self._extract_experience_years(cv_text),
            "education": self._extract_education(cv_text),
            "certifications": self._extract_certifications(cv_text),
            "projects": self._extract_projects(cv_text),
            "keywords": self._extract_keywords(cv_text)
        }
        return cv_data
    
    def parse_job_offer(self, job_text: str, job_title: str = "", 
                       company: str = "") -> Dict:
        """Extract structured requirements from job description"""
        job_data = {
            "title": job_title or self._extract_job_title(job_text),
            "company": company or self._extract_company(job_text),
            "required_skills": self._extract_required_skills(job_text),
            "preferred_skills": self._extract_preferred_skills(job_text),
            "required_experience": self._extract_required_experience(job_text),
            "education_required": self._extract_education_requirements(job_text),
            "certifications_required": self._extract_certification_requirements(job_text),
            "keywords": self._extract_job_keywords(job_text)
        }
        return job_data
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills from CV text"""
        text_lower = text.lower()
        found_skills = defaultdict(list)
        
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                # Check for whole word matches
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills[category].append(skill)
        
        return dict(found_skills)
    
    def _extract_experience_years(self, text: str) -> int:
        """Extract years of experience from CV"""
        # Look for patterns like "5 years", "3+ years", "2-4 years"
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience:\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+in'
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(m) for m in matches])
        
        return max(years) if years else 0
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education degrees from CV"""
        degrees = []
        degree_keywords = [
            r'\b(phd|ph\.d\.?|doctorate)\b',
            r'\b(master|masters|m\.s\.?|msc|ma|mba)\b',
            r'\b(bachelor|bachelors|b\.s\.?|bsc|ba|b\.a\.?)\b'
        ]
        
        text_lower = text.lower()
        for pattern in degree_keywords:
            if re.search(pattern, text_lower):
                match = re.search(pattern, text_lower)
                degrees.append(match.group(1))
        
        return degrees
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from CV"""
        cert_keywords = [
            "aws certified", "azure certified", "gcp certified",
            "cfa", "frm", "pmp", "tensorflow certified",
            "coursera", "udacity", "certification", "certified"
        ]
        
        certifications = []
        text_lower = text.lower()
        for cert in cert_keywords:
            if cert in text_lower:
                certifications.append(cert)
        
        return certifications
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract project descriptions"""
        # Look for project sections
        project_section = re.search(
            r'projects?:?\s*\n(.*?)(?:\n\n|\Z)', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        
        if project_section:
            return [p.strip() for p in project_section.group(1).split('\n') if p.strip()]
        return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from CV"""
        # Common important keywords
        keywords = set()
        
        important_terms = [
            "machine learning", "deep learning", "nlp", "computer vision",
            "data science", "artificial intelligence", "quantitative",
            "trading", "risk management", "portfolio", "deployment",
            "production", "scale", "optimization", "research"
        ]
        
        text_lower = text.lower()
        for term in important_terms:
            if term in text_lower:
                keywords.add(term)
        
        return list(keywords)
    
    def _extract_job_title(self, text: str) -> str:
        """Extract job title from job description"""
        # Look for common patterns
        patterns = [
            r'(?:position|role|title):\s*([^\n]+)',
            r'^([^\n]+?)(?:position|role)',
            r'hiring\s+(?:a|an)\s+([^\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        # Default to first line if no pattern matches
        return text.split('\n')[0].strip()[:100]
    
    def _extract_company(self, text: str) -> str:
        """Extract company name from job description"""
        patterns = [
            r'company:\s*([^\n]+)',
            r'(?:at|@)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "Unknown Company"
    
    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from job description"""
        required_skills = []
        text_lower = text.lower()
        
        # Look for required skills section
        required_section = re.search(
            r'(?:required|must have|requirements?).*?skills?:?\s*(.*?)(?:preferred|nice to have|responsibilities|\Z)',
            text_lower,
            re.DOTALL | re.IGNORECASE
        )
        
        search_text = required_section.group(1) if required_section else text_lower
        
        # Search for skills in the text
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, search_text):
                    required_skills.append(skill)
        
        return required_skills
    
    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred/nice-to-have skills"""
        preferred_skills = []
        text_lower = text.lower()
        
        # Look for preferred skills section
        preferred_section = re.search(
            r'(?:preferred|nice to have|bonus|plus).*?:?\s*(.*?)(?:responsibilities|about us|\Z)',
            text_lower,
            re.DOTALL | re.IGNORECASE
        )
        
        if preferred_section:
            search_text = preferred_section.group(1)
            
            for category, skills in self.SKILL_CATEGORIES.items():
                for skill in skills:
                    pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                    if re.search(pattern, search_text):
                        preferred_skills.append(skill)
        
        return preferred_skills
    
    def _extract_required_experience(self, text: str) -> int:
        """Extract required years of experience"""
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'minimum\s+(\d+)\s+years?',
            r'at least\s+(\d+)\s+years?'
        ]
        
        years = []
        text_lower = text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            years.extend([int(m) for m in matches])
        
        return min(years) if years else 0
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extract required education level"""
        text_lower = text.lower()
        requirements = []
        
        if re.search(r'\b(phd|ph\.d\.?|doctorate)\b', text_lower):
            requirements.append("phd")
        if re.search(r'\b(master|masters|m\.s\.?|graduate degree)\b', text_lower):
            requirements.append("masters")
        if re.search(r'\b(bachelor|bachelors|b\.s\.?|undergraduate degree)\b', text_lower):
            requirements.append("bachelors")
        
        return requirements
    
    def _extract_certification_requirements(self, text: str) -> List[str]:
        """Extract required certifications"""
        cert_patterns = [
            "aws certified", "azure certified", "gcp certified",
            "cfa", "frm", "pmp", "required certification"
        ]
        
        certifications = []
        text_lower = text.lower()
        for cert in cert_patterns:
            if cert in text_lower:
                certifications.append(cert)
        
        return certifications
    
    def _extract_job_keywords(self, text: str) -> List[str]:
        """Extract important keywords from job description"""
        keywords = set()
        
        keyword_patterns = [
            "machine learning", "deep learning", "nlp", "computer vision",
            "data science", "artificial intelligence", "quantitative",
            "trading", "risk management", "portfolio", "production",
            "scale", "research", "deployment", "optimization"
        ]
        
        text_lower = text.lower()
        for keyword in keyword_patterns:
            if keyword in text_lower:
                keywords.add(keyword)
        
        return list(keywords)
    
    def calculate_match_score(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Calculate comprehensive match score"""
        
        scores = {}
        
        # 1. Required Skills Match (35%)
        scores['required_skills'] = self._score_skills_match(
            cv_data['skills'], 
            job_data['required_skills']
        )
        
        # 2. Preferred Skills Match (15%)
        scores['preferred_skills'] = self._score_skills_match(
            cv_data['skills'],
            job_data['preferred_skills']
        )
        
        # 3. Experience Match (20%)
        scores['experience'] = self._score_experience_match(
            cv_data['experience_years'],
            job_data['required_experience']
        )
        
        # 4. Education Match (10%)
        scores['education'] = self._score_education_match(
            cv_data['education'],
            job_data['education_required']
        )
        
        # 5. Certifications Match (5%)
        scores['certifications'] = self._score_certifications_match(
            cv_data['certifications'],
            job_data['certifications_required']
        )
        
        # 6. Keywords Match (15%)
        scores['keywords'] = self._score_keywords_match(
            cv_data['keywords'],
            job_data['keywords']
        )
        
        # Calculate weighted total
        total_score = sum(
            scores[category] * self.WEIGHTS[category]
            for category in scores
        )
        
        return {
            "total_score": round(total_score, 2),
            "category_scores": scores,
            "weights": self.WEIGHTS
        }
    
    def _score_skills_match(self, cv_skills: Dict, required_skills: List[str]) -> float:
        """Score skills match (0-100)"""
        if not required_skills:
            return 100.0
        
        # Flatten CV skills
        cv_skills_flat = []
        for skills_list in cv_skills.values():
            cv_skills_flat.extend([s.lower() for s in skills_list])
        
        # Count matches
        matches = sum(1 for skill in required_skills if skill.lower() in cv_skills_flat)
        
        return (matches / len(required_skills)) * 100
    
    def _score_experience_match(self, cv_years: int, required_years: int) -> float:
        """Score experience match (0-100)"""
        if required_years == 0:
            return 100.0
        
        if cv_years >= required_years:
            return 100.0
        elif cv_years >= required_years * 0.8:
            return 80.0
        elif cv_years >= required_years * 0.6:
            return 60.0
        else:
            return (cv_years / required_years) * 50
    
    def _score_education_match(self, cv_education: List[str], 
                               required_education: List[str]) -> float:
        """Score education match (0-100)"""
        if not required_education:
            return 100.0
        
        education_levels = {"bachelors": 1, "masters": 2, "phd": 3}
        
        cv_level = max(
            [education_levels.get(e.lower().split()[0], 0) for e in cv_education],
            default=0
        )
        
        required_level = max(
            [education_levels.get(e.lower(), 0) for e in required_education],
            default=0
        )
        
        if cv_level >= required_level:
            return 100.0
        elif cv_level == required_level - 1:
            return 70.0
        else:
            return 40.0
    
    def _score_certifications_match(self, cv_certs: List[str], 
                                    required_certs: List[str]) -> float:
        """Score certifications match (0-100)"""
        if not required_certs:
            return 100.0
        
        cv_certs_lower = [c.lower() for c in cv_certs]
        matches = sum(1 for cert in required_certs if cert.lower() in cv_certs_lower)
        
        return (matches / len(required_certs)) * 100
    
    def _score_keywords_match(self, cv_keywords: List[str], 
                             job_keywords: List[str]) -> float:
        """Score keywords match (0-100)"""
        if not job_keywords:
            return 100.0
        
        cv_keywords_lower = [k.lower() for k in cv_keywords]
        matches = sum(1 for keyword in job_keywords if keyword.lower() in cv_keywords_lower)
        
        return (matches / len(job_keywords)) * 100
    
    def get_recommendation(self, score: float) -> Dict:
        """Get recommendation based on score"""
        if score >= self.THRESHOLDS["apply_now"]:
            return {
                "action": "APPLY NOW ✅",
                "confidence": "HIGH",
                "message": "Strong match! You have the required skills and experience. Apply immediately.",
                "priority": "high"
            }
        elif score >= self.THRESHOLDS["apply_caution"]:
            return {
                "action": "APPLY WITH CAUTION ⚠️",
                "confidence": "MEDIUM",
                "message": "Good match with some gaps. Highlight your transferable skills in your application.",
                "priority": "medium"
            }
        elif score >= self.THRESHOLDS["upskill_first"]:
            return {
                "action": "UPSKILL FIRST 📚",
                "confidence": "LOW",
                "message": "Significant skill gaps detected. Consider upskilling before applying.",
                "priority": "low"
            }
        else:
            return {
                "action": "NOT READY ❌",
                "confidence": "VERY LOW",
                "message": "Major gaps in requirements. Focus on building fundamental skills first.",
                "priority": "not_ready"
            }
    
    def generate_gap_analysis(self, cv_data: Dict, job_data: Dict, 
                             scores: Dict) -> Dict:
        """Generate detailed gap analysis with recommendations"""
        
        gaps = {
            "missing_required_skills": [],
            "missing_preferred_skills": [],
            "experience_gap": None,
            "education_gap": None,
            "missing_certifications": [],
            "recommendations": []
        }
        
        # 1. Skills gaps
        cv_skills_flat = []
        for skills_list in cv_data['skills'].values():
            cv_skills_flat.extend([s.lower() for s in skills_list])
        
        gaps["missing_required_skills"] = [
            skill for skill in job_data['required_skills']
            if skill.lower() not in cv_skills_flat
        ]
        
        gaps["missing_preferred_skills"] = [
            skill for skill in job_data['preferred_skills']
            if skill.lower() not in cv_skills_flat
        ]
        
        # 2. Experience gap
        if cv_data['experience_years'] < job_data['required_experience']:
            gaps["experience_gap"] = {
                "required": job_data['required_experience'],
                "current": cv_data['experience_years'],
                "deficit": job_data['required_experience'] - cv_data['experience_years']
            }
        
        # 3. Education gap
        education_levels = {"bachelors": 1, "masters": 2, "phd": 3}
        cv_level = max(
            [education_levels.get(e.lower().split()[0], 0) for e in cv_data['education']],
            default=0
        )
        required_level = max(
            [education_levels.get(e.lower(), 0) for e in job_data['education_required']],
            default=0
        )
        
        if cv_level < required_level:
            level_names = {1: "Bachelor's", 2: "Master's", 3: "PhD"}
            gaps["education_gap"] = {
                "required": level_names.get(required_level, "Unknown"),
                "current": level_names.get(cv_level, "None")
            }
        
        # 4. Certifications gap
        cv_certs_lower = [c.lower() for c in cv_data['certifications']]
        gaps["missing_certifications"] = [
            cert for cert in job_data['certifications_required']
            if cert.lower() not in cv_certs_lower
        ]
        
        # 5. Generate actionable recommendations
        gaps["recommendations"] = self._generate_recommendations(gaps, scores)
        
        return gaps
    
    def _generate_recommendations(self, gaps: Dict, scores: Dict) -> List[Dict]:
        """Generate prioritized recommendations for improvement"""
        recommendations = []
        
        # Priority 1: Critical required skills
        if gaps["missing_required_skills"]:
            top_missing = gaps["missing_required_skills"][:5]
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Required Skills",
                "action": f"Learn these essential skills: {', '.join(top_missing)}",
                "resources": self._get_learning_resources(top_missing),
                "estimated_time": "2-4 weeks per skill"
            })
        
        # Priority 2: Experience gap
        if gaps["experience_gap"]:
            deficit = gaps["experience_gap"]["deficit"]
            recommendations.append({
                "priority": "HIGH",
                "category": "Experience",
                "action": f"Gain {deficit} more years of relevant experience or highlight transferable projects",
                "resources": ["Work on personal projects", "Contribute to open source", "Freelance work"],
                "estimated_time": f"{deficit} years or equivalent project experience"
            })
        
        # Priority 3: Education gap
        if gaps["education_gap"]:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Education",
                "action": f"Consider pursuing {gaps['education_gap']['required']} degree or equivalent certifications",
                "resources": ["Online Master's programs", "Professional certifications", "Bootcamps"],
                "estimated_time": "6 months - 2 years"
            })
        
        # Priority 4: Preferred skills
        if gaps["missing_preferred_skills"]:
            top_preferred = gaps["missing_preferred_skills"][:3]
            recommendations.append({
                "priority": "LOW",
                "category": "Preferred Skills",
                "action": f"Nice to have: {', '.join(top_preferred)}",
                "resources": self._get_learning_resources(top_preferred),
                "estimated_time": "1-2 weeks per skill"
            })
        
        # Priority 5: Certifications
        if gaps["missing_certifications"]:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Certifications",
                "action": f"Obtain: {', '.join(gaps['missing_certifications'])}",
                "resources": ["Official certification programs", "Udemy", "Coursera"],
                "estimated_time": "1-3 months per certification"
            })
        
        return recommendations
    
    def _get_learning_resources(self, skills: List[str]) -> List[str]:
        """Get learning resources for specific skills"""
        resources = {
            "python": ["Python.org tutorials", "Real Python", "Codecademy Python"],
            "pytorch": ["PyTorch official tutorials", "Fast.ai", "Deep Learning with PyTorch"],
            "tensorflow": ["TensorFlow documentation", "Coursera TensorFlow courses"],
            "aws": ["AWS Training", "A Cloud Guru", "AWS Certified Solutions Architect"],
            "docker": ["Docker documentation", "Docker Mastery on Udemy"],
            "kubernetes": ["Kubernetes documentation", "CKA certification prep"],
        }
        
        result = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in resources:
                result.extend(resources[skill_lower])
            else:
                result.append(f"Search for '{skill}' courses on Coursera/Udemy")
        
        return list(set(result))[:3]
    
    def analyze_job(self, cv_text: str, job_text: str, 
                   job_title: str = "", company: str = "") -> Dict:
        """Complete analysis: parse, score, and provide recommendations"""
        
        # Parse inputs
        cv_data = self.parse_cv(cv_text)
        job_data = self.parse_job_offer(job_text, job_title, company)
        
        # Calculate scores
        score_result = self.calculate_match_score(cv_data, job_data)
        total_score = score_result["total_score"]
        
        # Get recommendation
        recommendation = self.get_recommendation(total_score)
        
        # Generate gap analysis
        gaps = self.generate_gap_analysis(cv_data, job_data, score_result)
        
        # Compile result
        result = {
            "analysis_date": datetime.now().isoformat(),
            "job_info": {
                "title": job_data["title"],
                "company": job_data["company"]
            },
            "score": score_result,
            "recommendation": recommendation,
            "gaps": gaps,
            "cv_summary": {
                "skills_count": sum(len(v) for v in cv_data['skills'].values()),
                "experience_years": cv_data['experience_years'],
                "education_level": cv_data['education'][0] if cv_data['education'] else "Not specified"
            },
            "job_requirements": {
                "required_skills_count": len(job_data['required_skills']),
                "preferred_skills_count": len(job_data['preferred_skills']),
                "experience_required": job_data['required_experience']
            }
        }
        
        # Save result
        self.matches.append(result)
        self._save_json(self.results_file, self.matches)
        
        return result
    
    def generate_report(self, result: Dict) -> str:
        """Generate detailed analysis report"""
        
        score = result['score']['total_score']
        recommendation = result['recommendation']
        gaps = result['gaps']
        
        report = f"""
{'='*80}
CV vs JOB OFFER ANALYSIS REPORT
{'='*80}

Job: {result['job_info']['title']}
Company: {result['job_info']['company']}
Date: {datetime.fromisoformat(result['analysis_date']).strftime('%Y-%m-%d %H:%M')}

{'='*80}
OVERALL MATCH SCORE: {score}%
{'='*80}

Recommendation: {recommendation['action']}
Confidence: {recommendation['confidence']}
Message: {recommendation['message']}

{'='*80}
DETAILED SCORES
{'='*80}
"""
        
        for category, cat_score in result['score']['category_scores'].items():
            weight = result['score']['weights'][category]
            contribution = cat_score * weight
            report += f"\n{category.replace('_', ' ').title():<25} {cat_score:>5.1f}%  (Weight: {weight:.0%}, Contribution: {contribution:.1f}%)"
        
        report += f"\n\n{'='*80}\nGAP ANALYSIS\n{'='*80}\n"
        
        if gaps['missing_required_skills']:
            report += f"\n❌ Missing REQUIRED Skills ({len(gaps['missing_required_skills'])}):\n"
            for skill in gaps['missing_required_skills'][:10]:
                report += f"   - {skill}\n"
        
        if gaps['missing_preferred_skills']:
            report += f"\n⚠️  Missing PREFERRED Skills ({len(gaps['missing_preferred_skills'])}):\n"
            for skill in gaps['missing_preferred_skills'][:5]:
                report += f"   - {skill}\n"
        
        if gaps['experience_gap']:
            exp_gap = gaps['experience_gap']
            report += f"\n📊 Experience Gap:\n"
            report += f"   Required: {exp_gap['required']} years\n"
            report += f"   Current: {exp_gap['current']} years\n"
            report += f"   Deficit: {exp_gap['deficit']} years\n"
        
        if gaps['education_gap']:
            edu_gap = gaps['education_gap']
            report += f"\n🎓 Education Gap:\n"
            report += f"   Required: {edu_gap['required']}\n"
            report += f"   Current: {edu_gap['current']}\n"
        
        if gaps['missing_certifications']:
            report += f"\n📜 Missing Certifications:\n"
            for cert in gaps['missing_certifications']:
                report += f"   - {cert}\n"
        
        report += f"\n{'='*80}\nACTION PLAN\n{'='*80}\n"
        
        for i, rec in enumerate(gaps['recommendations'], 1):
            report += f"\n{i}. [{rec['priority']}] {rec['category']}\n"
            report += f"   Action: {rec['action']}\n"
            report += f"   Time: {rec['estimated_time']}\n"
            if rec['resources']:
                report += f"   Resources:\n"
                for resource in rec['resources'][:3]:
                    report += f"      • {resource}\n"
        
        report += f"\n{'='*80}\n"
        
        return report
    
    def batch_analyze(self, cv_text: str, jobs: List[Dict]) -> List[Dict]:
        """Analyze CV against multiple job offers"""
        results = []
        
        for job in jobs:
            result = self.analyze_job(
                cv_text,
                job['description'],
                job.get('title', ''),
                job.get('company', '')
            )
            results.append(result)
        
        # Sort by score
        results.sort(key=lambda x: x['score']['total_score'], reverse=True)
        
        return results
    
    def compare_jobs(self, cv_text: str, jobs: List[Dict]) -> str:
        """Compare multiple jobs and rank them"""
        results = self.batch_analyze(cv_text, jobs)
        
        report = f"""
{'='*80}
JOB COMPARISON REPORT
{'='*80}
Analyzed {len(results)} job offers against your CV
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*80}
RANKED RESULTS
{'='*80}

"""
        
        for i, result in enumerate(results, 1):
            score = result['score']['total_score']
            job_info = result['job_info']
            rec = result['recommendation']
            
            report += f"\n{i}. {job_info['title']} - {job_info['company']}\n"
            report += f"   Score: {score}% | {rec['action']}\n"
            report += f"   Missing Required Skills: {len(result['gaps']['missing_required_skills'])}\n"
            report += f"   Priority: {rec['priority'].upper()}\n"
            report += f"   {'-'*76}\n"
        
        report += f"\n{'='*80}\nRECOMMENDATIONS\n{'='*80}\n"
        
        # Top picks
        top_picks = [r for r in results if r['score']['total_score'] >= 75]
        if top_picks:
            report += f"\n✅ APPLY IMMEDIATELY ({len(top_picks)} jobs):\n"
            for r in top_picks:
                report += f"   • {r['job_info']['title']} at {r['job_info']['company']} ({r['score']['total_score']}%)\n"
        
        # Good matches
        good_matches = [r for r in results if 60 <= r['score']['total_score'] < 75]
        if good_matches:
            report += f"\n⚠️  APPLY WITH PREPARATION ({len(good_matches)} jobs):\n"
            for r in good_matches:
                report += f"   • {r['job_info']['title']} at {r['job_info']['company']} ({r['score']['total_score']}%)\n"
        
        # Need upskilling
        upskill = [r for r in results if 40 <= r['score']['total_score'] < 60]
        if upskill:
            report += f"\n📚 UPSKILL FIRST ({len(upskill)} jobs):\n"
            for r in upskill:
                report += f"   • {r['job_info']['title']} at {r['job_info']['company']} ({r['score']['total_score']}%)\n"
        
        return report


def main():
    """Interactive CLI for CV-Job matching"""
    import sys
    
    matcher = CVJobMatcher()
    
    def print_menu():
        print("\n" + "="*80)
        print("CV vs JOB OFFER MATCHER & SCORER")
        print("="*80)
        print("1. Analyze Single Job Offer")
        print("2. Compare Multiple Job Offers")
        print("3. View Past Analyses")
        print("4. Load CV from File")
        print("5. Load Job Description from File")
        print("6. Adjust Scoring Thresholds")
        print("7. Export Analysis Report")
        print("0. Exit")
        print("="*80)
    
    cv_text = ""
    job_text = ""
    
    def load_cv_interactive():
        nonlocal cv_text
        print("\n--- Load CV ---")
        print("1. Paste CV text")
        print("2. Load from file")
        choice = input("Choose option: ")
        
        if choice == "1":
            print("\nPaste your CV (press Ctrl+D or Ctrl+Z when done):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            cv_text = "\n".join(lines)
            print(f"✓ CV loaded ({len(cv_text)} characters)")
        
        elif choice == "2":
            filepath = input("Enter CV file path: ")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
                print(f"✓ CV loaded from {filepath} ({len(cv_text)} characters)")
            except FileNotFoundError:
                print("❌ File not found")
    
    def load_job_interactive():
        nonlocal job_text
        print("\n--- Load Job Description ---")
        print("1. Paste job description")
        print("2. Load from file")
        choice = input("Choose option: ")
        
        if choice == "1":
            print("\nPaste job description (press Ctrl+D or Ctrl+Z when done):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            job_text = "\n".join(lines)
            print(f"✓ Job description loaded ({len(job_text)} characters)")
        
        elif choice == "2":
            filepath = input("Enter job file path: ")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    job_text = f.read()
                print(f"✓ Job loaded from {filepath} ({len(job_text)} characters)")
            except FileNotFoundError:
                print("❌ File not found")
    
    def analyze_single_job():
        if not cv_text:
            print("❌ Please load CV first (option 4)")
            return
        if not job_text:
            print("❌ Please load job description first (option 5)")
            return
        
        print("\n--- Analyzing Job Offer ---")
        job_title = input("Job title (optional): ")
        company = input("Company name (optional): ")
        
        print("\n⏳ Analyzing...")
        result = matcher.analyze_job(cv_text, job_text, job_title, company)
        
        report = matcher.generate_report(result)
        print(report)
        
        # Save to file
        save = input("\nSave report to file? (y/n): ")
        if save.lower() == 'y':
            filename = f"job_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = matcher.data_dir / filename
            with open(filepath, 'w') as f:
                f.write(report)
            print(f"✓ Report saved to {filepath}")
    
    def compare_multiple_jobs():
        if not cv_text:
            print("❌ Please load CV first (option 4)")
            return
        
        print("\n--- Compare Multiple Jobs ---")
        num_jobs = int(input("How many jobs to compare? "))
        
        jobs = []
        for i in range(num_jobs):
            print(f"\n--- Job {i+1} ---")
            title = input("Job title: ")
            company = input("Company: ")
            print("Paste job description (Ctrl+D or Ctrl+Z when done):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            description = "\n".join(lines)
            
            jobs.append({
                "title": title,
                "company": company,
                "description": description
            })
        
        print("\n⏳ Analyzing all jobs...")
        report = matcher.compare_jobs(cv_text, jobs)
        print(report)
        
        # Save to file
        save = input("\nSave comparison report to file? (y/n): ")
        if save.lower() == 'y':
            filename = f"job_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = matcher.data_dir / filename
            with open(filepath, 'w') as f:
                f.write(report)
            print(f"✓ Report saved to {filepath}")
    
    def view_past_analyses():
        if not matcher.matches:
            print("\n❌ No past analyses found")
            return
        
        print("\n--- Past Analyses ---")
        for i, match in enumerate(matcher.matches[-10:], 1):
            score = match['score']['total_score']
            job_info = match['job_info']
            date = datetime.fromisoformat(match['analysis_date']).strftime('%Y-%m-%d')
            
            print(f"\n{i}. {job_info['title']} - {job_info['company']}")
            print(f"   Score: {score}% | {match['recommendation']['action']}")
            print(f"   Date: {date}")
        
        view_detail = input("\nView detailed report? Enter number (or 0 to skip): ")
        if view_detail.isdigit() and 1 <= int(view_detail) <= len(matcher.matches[-10:]):
            idx = int(view_detail) - 1
            result = matcher.matches[-(10-idx)]
            report = matcher.generate_report(result)
            print(report)
    
    def adjust_thresholds():
        print("\n--- Current Thresholds ---")
        print(f"Apply Now (Strong Match): {matcher.THRESHOLDS['apply_now']}%")
        print(f"Apply with Caution: {matcher.THRESHOLDS['apply_caution']}%")
        print(f"Upskill First: {matcher.THRESHOLDS['upskill_first']}%")
        
        adjust = input("\nAdjust thresholds? (y/n): ")
        if adjust.lower() == 'y':
            try:
                matcher.THRESHOLDS['apply_now'] = int(input("Apply Now threshold (current 75): ") or "75")
                matcher.THRESHOLDS['apply_caution'] = int(input("Apply Caution threshold (current 60): ") or "60")
                matcher.THRESHOLDS['upskill_first'] = int(input("Upskill First threshold (current 40): ") or "40")
                print("✓ Thresholds updated")
            except ValueError:
                print("❌ Invalid input")
    
    def export_report():
        if not matcher.matches:
            print("\n❌ No analyses to export")
            return
        
        print("\n--- Export Options ---")
        print("1. Export latest analysis")
        print("2. Export all analyses")
        choice = input("Choose option: ")
        
        if choice == "1" and matcher.matches:
            result = matcher.matches[-1]
            report = matcher.generate_report(result)
            filename = f"cv_job_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = matcher.data_dir / filename
            with open(filepath, 'w') as f:
                f.write(report)
            print(f"✓ Report exported to {filepath}")
        
        elif choice == "2":
            filename = f"all_analyses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = matcher.data_dir / filename
            with open(filepath, 'w') as f:
                json.dump(matcher.matches, f, indent=2)
            print(f"✓ All analyses exported to {filepath}")
    
    # Main loop
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Demo mode
        print("Running demo mode...")
        
        demo_cv = """
        John Doe
        Machine Learning Engineer
        
        Experience: 3 years in ML/AI
        
        Skills: Python, PyTorch, TensorFlow, Scikit-learn, AWS, Docker, Kubernetes
        Natural Language Processing, Computer Vision, MLOps
        
        Education: Master's in Computer Science
        
        Projects:
        - Built LLM-based chatbot using GPT-3.5
        - Developed computer vision system for object detection
        - Deployed ML models on AWS SageMaker
        """
        
        demo_job = """
        Senior Machine Learning Engineer
        Company: Tech Innovations Inc.
        
        Requirements:
        - 5+ years of experience in ML/AI
        - Strong programming skills in Python
        - Experience with PyTorch or TensorFlow
        - Deep Learning, NLP, Computer Vision
        - Cloud platforms (AWS, GCP, or Azure)
        - Docker and Kubernetes
        - PhD or Master's in CS/related field
        
        Preferred:
        - Experience with LLMs
        - MLOps experience
        - Production ML deployment
        """
        
        result = matcher.analyze_job(demo_cv, demo_job, "Senior ML Engineer", "Tech Innovations")
        report = matcher.generate_report(result)
        print(report)
    
    else:
        # Interactive mode
        while True:
            print_menu()
            choice = input("\nSelect option: ")
            
            if choice == "0":
                print("Exiting...")
                break
            elif choice == "1":
                analyze_single_job()
            elif choice == "2":
                compare_multiple_jobs()
            elif choice == "3":
                view_past_analyses()
            elif choice == "4":
                load_cv_interactive()
            elif choice == "5":
                load_job_interactive()
            elif choice == "6":
                adjust_thresholds()
            elif choice == "7":
                export_report()
            else:
                print("❌ Invalid option")
            
            if choice != "0":
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
