#!/usr/bin/env python3
"""
Glassdoor Research Automation
Automated company research, salary analysis, and interview prep
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import statistics

class GlassdoorAutomation:
    def __init__(self, data_dir: str = "job_search"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Data files
        self.companies_file = self.data_dir / "glassdoor_companies.json"
        self.salaries_file = self.data_dir / "glassdoor_salaries.json"
        self.interviews_file = self.data_dir / "glassdoor_interviews.json"
        self.reviews_file = self.data_dir / "glassdoor_reviews.json"
        self.research_queue_file = self.data_dir / "glassdoor_queue.json"
        
        self.companies = self._load_json(self.companies_file, [])
        self.salaries = self._load_json(self.salaries_file, [])
        self.interviews = self._load_json(self.interviews_file, [])
        self.reviews = self._load_json(self.reviews_file, [])
        self.research_queue = self._load_json(self.research_queue_file, [])
    
    def _load_json(self, filepath: Path, default):
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, filepath: Path, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_company_to_research(self, company_name: str, priority: str = "medium",
                               reason: str = "job_application", 
                               specific_role: str = None) -> Dict:
        """Add company to research queue"""
        
        # Check if already researched
        existing = self._get_company(company_name)
        if existing:
            return {
                "success": False,
                "message": "Company already researched",
                "company_id": existing["id"],
                "last_updated": existing["last_updated"]
            }
        
        company_id = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        research_item = {
            "id": company_id,
            "company_name": company_name,
            "priority": priority,
            "reason": reason,
            "specific_role": specific_role,
            "added_date": datetime.now().isoformat(),
            "status": "queued",
            "research_checklist": {
                "company_overview": False,
                "salary_data": False,
                "interview_questions": False,
                "employee_reviews": False,
                "culture_insights": False,
                "benefits_perks": False,
                "interview_difficulty": False,
                "hiring_process": False
            }
        }
        
        self.research_queue.append(research_item)
        self._save_json(self.research_queue_file, self.research_queue)
        
        return {
            "success": True,
            "company_id": company_id,
            "message": f"Added {company_name} to research queue",
            "checklist": research_item["research_checklist"]
        }
    
    def log_company_data(self, company_name: str, data_type: str, data: Dict) -> Dict:
        """Log researched data about a company"""
        
        company = self._get_company(company_name)
        
        if not company:
            # Create new company entry
            company_id = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            company = {
                "id": company_id,
                "company_name": company_name,
                "overall_rating": None,
                "last_updated": datetime.now().isoformat(),
                "research_completed": datetime.now().isoformat(),
                "data_sources": []
            }
            self.companies.append(company)
        
        # Update based on data type
        if data_type == "overview":
            company.update({
                "industry": data.get("industry"),
                "size": data.get("size"),
                "founded": data.get("founded"),
                "headquarters": data.get("headquarters"),
                "overall_rating": data.get("overall_rating"),
                "ceo_approval": data.get("ceo_approval"),
                "recommend_to_friend": data.get("recommend_to_friend"),
                "website": data.get("website")
            })
            self._update_checklist(company_name, "company_overview")
        
        elif data_type == "salary":
            salary_entry = {
                "company_id": company["id"],
                "company_name": company_name,
                "role": data.get("role"),
                "base_salary_min": data.get("base_salary_min"),
                "base_salary_max": data.get("base_salary_max"),
                "base_salary_avg": data.get("base_salary_avg"),
                "total_comp_min": data.get("total_comp_min"),
                "total_comp_max": data.get("total_comp_max"),
                "total_comp_avg": data.get("total_comp_avg"),
                "bonus": data.get("bonus"),
                "stock": data.get("stock"),
                "location": data.get("location"),
                "experience_level": data.get("experience_level"),
                "data_points": data.get("data_points", 1),
                "logged_date": datetime.now().isoformat()
            }
            self.salaries.append(salary_entry)
            self._save_json(self.salaries_file, self.salaries)
            self._update_checklist(company_name, "salary_data")
        
        elif data_type == "interview":
            interview_entry = {
                "company_id": company["id"],
                "company_name": company_name,
                "role": data.get("role"),
                "overall_experience": data.get("overall_experience"),
                "difficulty": data.get("difficulty"),
                "process_length": data.get("process_length"),
                "interview_rounds": data.get("interview_rounds", []),
                "questions_asked": data.get("questions_asked", []),
                "offer_received": data.get("offer_received"),
                "logged_date": datetime.now().isoformat()
            }
            self.interviews.append(interview_entry)
            self._save_json(self.interviews_file, self.interviews)
            self._update_checklist(company_name, "interview_questions")
            self._update_checklist(company_name, "interview_difficulty")
            self._update_checklist(company_name, "hiring_process")
        
        elif data_type == "review":
            review_entry = {
                "company_id": company["id"],
                "company_name": company_name,
                "role": data.get("role"),
                "rating": data.get("rating"),
                "work_life_balance": data.get("work_life_balance"),
                "culture_values": data.get("culture_values"),
                "career_opportunities": data.get("career_opportunities"),
                "comp_benefits": data.get("comp_benefits"),
                "senior_management": data.get("senior_management"),
                "pros": data.get("pros", []),
                "cons": data.get("cons", []),
                "advice_to_management": data.get("advice_to_management"),
                "employment_status": data.get("employment_status"),
                "logged_date": datetime.now().isoformat()
            }
            self.reviews.append(review_entry)
            self._save_json(self.reviews_file, self.reviews)
            self._update_checklist(company_name, "employee_reviews")
            self._update_checklist(company_name, "culture_insights")
        
        elif data_type == "benefits":
            company["benefits"] = data.get("benefits", [])
            company["perks"] = data.get("perks", [])
            self._update_checklist(company_name, "benefits_perks")
        
        company["last_updated"] = datetime.now().isoformat()
        self._save_json(self.companies_file, self.companies)
        
        return {
            "success": True,
            "message": f"Logged {data_type} data for {company_name}",
            "company_id": company["id"]
        }
    
    def get_salary_insights(self, company_name: str, role: str = None) -> Dict:
        """Get salary insights for a company/role"""
        
        # Filter salaries
        if role:
            company_salaries = [
                s for s in self.salaries 
                if s["company_name"].lower() == company_name.lower() 
                and role.lower() in s["role"].lower()
            ]
        else:
            company_salaries = [
                s for s in self.salaries 
                if s["company_name"].lower() == company_name.lower()
            ]
        
        if not company_salaries:
            return {
                "success": False,
                "message": f"No salary data for {company_name}" + (f" - {role}" if role else "")
            }
        
        # Calculate insights
        base_salaries = [s["base_salary_avg"] for s in company_salaries if s.get("base_salary_avg")]
        total_comps = [s["total_comp_avg"] for s in company_salaries if s.get("total_comp_avg")]
        
        insights = {
            "company_name": company_name,
            "role_filter": role,
            "data_points": len(company_salaries),
            "base_salary": {
                "min": min(base_salaries) if base_salaries else None,
                "max": max(base_salaries) if base_salaries else None,
                "average": statistics.mean(base_salaries) if base_salaries else None,
                "median": statistics.median(base_salaries) if base_salaries else None
            },
            "total_compensation": {
                "min": min(total_comps) if total_comps else None,
                "max": max(total_comps) if total_comps else None,
                "average": statistics.mean(total_comps) if total_comps else None,
                "median": statistics.median(total_comps) if total_comps else None
            },
            "by_location": {},
            "by_experience": {}
        }
        
        # Break down by location
        locations = set(s["location"] for s in company_salaries if s.get("location"))
        for loc in locations:
            loc_salaries = [s["total_comp_avg"] for s in company_salaries 
                          if s.get("location") == loc and s.get("total_comp_avg")]
            if loc_salaries:
                insights["by_location"][loc] = {
                    "average": statistics.mean(loc_salaries),
                    "count": len(loc_salaries)
                }
        
        # Break down by experience
        exp_levels = set(s["experience_level"] for s in company_salaries if s.get("experience_level"))
        for exp in exp_levels:
            exp_salaries = [s["total_comp_avg"] for s in company_salaries 
                          if s.get("experience_level") == exp and s.get("total_comp_avg")]
            if exp_salaries:
                insights["by_experience"][exp] = {
                    "average": statistics.mean(exp_salaries),
                    "count": len(exp_salaries)
                }
        
        return insights
    
    def get_interview_prep(self, company_name: str, role: str = None) -> Dict:
        """Get interview preparation insights"""
        
        # Filter interviews
        if role:
            company_interviews = [
                i for i in self.interviews 
                if i["company_name"].lower() == company_name.lower() 
                and role.lower() in i["role"].lower()
            ]
        else:
            company_interviews = [
                i for i in self.interviews 
                if i["company_name"].lower() == company_name.lower()
            ]
        
        if not company_interviews:
            return {
                "success": False,
                "message": f"No interview data for {company_name}" + (f" - {role}" if role else "")
            }
        
        # Aggregate questions
        all_questions = []
        for interview in company_interviews:
            all_questions.extend(interview.get("questions_asked", []))
        
        # Count question frequency
        question_frequency = {}
        for q in all_questions:
            question_frequency[q] = question_frequency.get(q, 0) + 1
        
        # Sort by frequency
        common_questions = sorted(question_frequency.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate difficulty distribution
        difficulties = [i["difficulty"] for i in company_interviews if i.get("difficulty")]
        difficulty_dist = {
            "easy": difficulties.count("easy"),
            "medium": difficulties.count("medium"),
            "hard": difficulties.count("hard")
        }
        
        # Calculate experience distribution
        experiences = [i["overall_experience"] for i in company_interviews if i.get("overall_experience")]
        experience_dist = {
            "positive": experiences.count("positive"),
            "neutral": experiences.count("neutral"),
            "negative": experiences.count("negative")
        }
        
        # Offer rate
        offers = [i["offer_received"] for i in company_interviews if i.get("offer_received") is not None]
        offer_rate = (offers.count(True) / len(offers) * 100) if offers else None
        
        # Average process length
        process_lengths = [i["process_length"] for i in company_interviews if i.get("process_length")]
        avg_process = statistics.mean(process_lengths) if process_lengths else None
        
        # Interview rounds analysis
        all_rounds = []
        for interview in company_interviews:
            all_rounds.extend(interview.get("interview_rounds", []))
        
        prep_guide = {
            "company_name": company_name,
            "role_filter": role,
            "total_interviews_analyzed": len(company_interviews),
            "difficulty_distribution": difficulty_dist,
            "experience_distribution": experience_dist,
            "offer_rate": f"{offer_rate:.1f}%" if offer_rate else "Unknown",
            "average_process_length": f"{avg_process:.1f} days" if avg_process else "Unknown",
            "most_common_questions": [
                {"question": q, "frequency": f} 
                for q, f in common_questions[:15]
            ],
            "interview_rounds": list(set(all_rounds)),
            "preparation_tips": self._generate_prep_tips(
                difficulty_dist, common_questions, all_rounds
            )
        }
        
        return prep_guide
    
    def _generate_prep_tips(self, difficulty_dist: Dict, 
                           common_questions: List, rounds: List) -> List[str]:
        """Generate interview preparation tips"""
        
        tips = []
        
        # Difficulty-based tips
        if difficulty_dist.get("hard", 0) > difficulty_dist.get("easy", 0):
            tips.append("⚠️ Interviews are reported as challenging - allocate extra prep time")
            tips.append("📚 Review fundamentals deeply and practice advanced problems")
        elif difficulty_dist.get("easy", 0) > difficulty_dist.get("hard", 0):
            tips.append("✅ Interviews are generally manageable - focus on clear communication")
        
        # Question-based tips
        if common_questions:
            tips.append(f"🎯 Top question asked {common_questions[0][1]} times - prepare thoroughly")
        
        # Round-based tips
        if "technical_screen" in rounds:
            tips.append("💻 Expect technical screening - brush up on coding/problem-solving")
        if "system_design" in rounds:
            tips.append("�️ System design round likely - review scalability patterns")
        if "behavioral" in rounds:
            tips.append("🗣️ Behavioral interviews included - prepare STAR stories")
        if "case_study" in rounds:
            tips.append("📊 Case study expected - practice structured problem-solving")
        
        return tips
    
    def get_company_culture_report(self, company_name: str) -> Dict:
        """Generate comprehensive culture report"""
        
        company = self._get_company(company_name)
        if not company:
            return {"success": False, "message": f"No data for {company_name}"}
        
        # Get all reviews
        company_reviews = [
            r for r in self.reviews 
            if r["company_name"].lower() == company_name.lower()
        ]
        
        if not company_reviews:
            return {"success": False, "message": f"No reviews for {company_name}"}
        
        # Calculate average ratings
        ratings = {
            "overall": [],
            "work_life_balance": [],
            "culture_values": [],
            "career_opportunities": [],
            "comp_benefits": [],
            "senior_management": []
        }
        
        for review in company_reviews:
            ratings["overall"].append(review.get("rating", 0))
            ratings["work_life_balance"].append(review.get("work_life_balance", 0))
            ratings["culture_values"].append(review.get("culture_values", 0))
            ratings["career_opportunities"].append(review.get("career_opportunities", 0))
            ratings["comp_benefits"].append(review.get("comp_benefits", 0))
            ratings["senior_management"].append(review.get("senior_management", 0))
        
        avg_ratings = {
            key: statistics.mean([r for r in vals if r > 0]) if vals else 0
            for key, vals in ratings.items()
        }
        
        # Aggregate pros and cons
        all_pros = []
        all_cons = []
        for review in company_reviews:
            all_pros.extend(review.get("pros", []))
            all_cons.extend(review.get("cons", []))
        
        # Current vs Former employee split
        current_count = sum(1 for r in company_reviews if r.get("employment_status") == "current")
        former_count = sum(1 for r in company_reviews if r.get("employment_status") == "former")
        
        culture_report = {
            "company_name": company_name,
            "overall_rating": company.get("overall_rating"),
            "ceo_approval": company.get("ceo_approval"),
            "recommend_to_friend": company.get("recommend_to_friend"),
            "total_reviews_analyzed": len(company_reviews),
            "current_employees": current_count,
            "former_employees": former_count,
            "average_ratings": {
                key: f"{val:.1f}/5.0" for key, val in avg_ratings.items()
            },
            "top_pros": self._count_frequency(all_pros)[:5],
            "top_cons": self._count_frequency(all_cons)[:5],
            "strengths": self._identify_strengths(avg_ratings),
            "concerns": self._identify_concerns(avg_ratings),
            "culture_summary": self._generate_culture_summary(avg_ratings, all_pros, all_cons)
        }
        
        return culture_report
    
    def _count_frequency(self, items: List[str]) -> List[Dict]:
        """Count frequency of items"""
        frequency = {}
        for item in items:
            item_lower = item.lower().strip()
            frequency[item_lower] = frequency.get(item_lower, 0) + 1
        
        sorted_items = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        return [{"item": item, "count": count} for item, count in sorted_items]
    
    def _identify_strengths(self, ratings: Dict) -> List[str]:
        """Identify company strengths based on ratings"""
        strengths = []
        
        for category, rating in ratings.items():
            if rating >= 4.0:
                strengths.append(f"Strong {category.replace('_', ' ')}: {rating:.1f}/5.0")
        
        return strengths
    
    def _identify_concerns(self, ratings: Dict) -> List[str]:
        """Identify potential concerns"""
        concerns = []
        
        for category, rating in ratings.items():
            if rating < 3.0:
                concerns.append(f"Lower {category.replace('_', ' ')}: {rating:.1f}/5.0")
        
        return concerns
    
    def _generate_culture_summary(self, ratings: Dict, pros: List, cons: List) -> str:
        """Generate AI-style culture summary"""
        
        # Simple heuristic-based summary
        wlb = ratings.get("work_life_balance", 0)
        culture = ratings.get("culture_values", 0)
        career = ratings.get("career_opportunities", 0)
        comp = ratings.get("comp_benefits", 0)
        mgmt = ratings.get("senior_management", 0)
        
        summary_parts = []
        
        if wlb >= 4.0:
            summary_parts.append("Excellent work-life balance")
        elif wlb < 3.0:
            summary_parts.append("Work-life balance may be challenging")
        
        if culture >= 4.0:
            summary_parts.append("strong culture and values")
        
        if career >= 4.0:
            summary_parts.append("good career growth opportunities")
        elif career < 3.0:
            summary_parts.append("limited career advancement")
        
        if comp >= 4.0:
            summary_parts.append("competitive compensation and benefits")
        
        if mgmt < 3.0:
            summary_parts.append("some concerns about senior leadership")
        
        if not summary_parts:
            return "Mixed reviews across categories - research further"
        
        return ". ".join(summary_parts).capitalize() + "."
    
    def get_research_checklist(self, company_name: str) -> Dict:
        """Get research progress checklist"""
        
        queue_item = None
        for item in self.research_queue:
            if item["company_name"].lower() == company_name.lower():
                queue_item = item
                break
        
        if not queue_item:
            return {"success": False, "message": f"{company_name} not in research queue"}
        
        checklist = queue_item["research_checklist"]
        completed = sum(1 for v in checklist.values() if v)
        total = len(checklist)
        progress = (completed / total * 100)
        
        return {
            "company_name": company_name,
            "progress": f"{progress:.0f}%",
            "completed": completed,
            "total": total,
            "checklist": checklist,
            "next_steps": [k for k, v in checklist.items() if not v]
        }
    
    def _update_checklist(self, company_name: str, item: str):
        """Update research checklist"""
        for queue_item in self.research_queue:
            if queue_item["company_name"].lower() == company_name.lower():
                if item in queue_item["research_checklist"]:
                    queue_item["research_checklist"][item] = True
                
                # Check if all complete
                if all(queue_item["research_checklist"].values()):
                    queue_item["status"] = "completed"
                    queue_item["completed_date"] = datetime.now().isoformat()
                
                self._save_json(self.research_queue_file, self.research_queue)
                break
    
    def _get_company(self, company_name: str) -> Optional[Dict]:
        """Get company by name"""
        for company in self.companies:
            if company["company_name"].lower() == company_name.lower():
                return company
        return None
    
    def generate_full_research_report(self, company_name: str) -> str:
        """Generate comprehensive research report"""
        
        company = self._get_company(company_name)
        if not company:
            return f"No research data available for {company_name}"
        
        report = f"""
# Glassdoor Research Report: {company_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Company Overview
"""
        
        if company.get("overall_rating"):
            report += f"- Overall Rating: {company['overall_rating']}/5.0\n"
        if company.get("ceo_approval"):
            report += f"- CEO Approval: {company['ceo_approval']}%\n"
        if company.get("recommend_to_friend"):
            report += f"- Would Recommend: {company['recommend_to_friend']}%\n"
        if company.get("industry"):
            report += f"- Industry: {company['industry']}\n"
        if company.get("size"):
            report += f"- Size: {company['size']} employees\n"
        if company.get("headquarters"):
            report += f"- Headquarters: {company['headquarters']}\n"
        
        # Salary insights
        report += "\n## Salary & Compensation\n"
        company_salaries = [s for s in self.salaries if s["company_name"] == company_name]
        
        if company_salaries:
            roles_analyzed = set(s["role"] for s in company_salaries)
            report += f"- Roles Analyzed: {len(roles_analyzed)}\n"
            report += f"- Total Data Points: {len(company_salaries)}\n\n"
            
            for role in list(roles_analyzed)[:5]:
                insights = self.get_salary_insights(company_name, role)
                if insights.get("total_compensation", {}).get("average"):
                    avg_comp = insights["total_compensation"]["average"]
                    report += f"### {role}\n"
                    report += f"- Average Total Comp: ${avg_comp:,.0f}\n"
                    
                    if insights.get("base_salary", {}).get("average"):
                        report += f"- Average Base: ${insights['base_salary']['average']:,.0f}\n"
                    
                    report += "\n"
        else:
            report += "No salary data available\n"
        
        # Interview insights
        report += "\n## Interview Process\n"
        company_interviews = [i for i in self.interviews if i["company_name"] == company_name]
        
        if company_interviews:
            prep = self.get_interview_prep(company_name)
            report += f"- Interviews Analyzed: {prep['total_interviews_analyzed']}\n"
            report += f"- Difficulty: {self._format_difficulty_dist(prep['difficulty_distribution'])}\n"
            report += f"- Average Process Length: {prep['average_process_length']}\n"
            report += f"- Offer Rate: {prep['offer_rate']}\n\n"
            
            if prep["most_common_questions"]:
                report += "### Most Common Interview Questions:\n"
                for q in prep["most_common_questions"][:10]:
                    report += f"{q['frequency']}. {q['question']}\n"
            
            if prep["preparation_tips"]:
                report += "\n### Preparation Tips:\n"
                for tip in prep["preparation_tips"]:
                    report += f"- {tip}\n"
        else:
            report += "No interview data available\n"
        
        # Culture insights
        report += "\n## Company Culture & Reviews\n"
        culture = self.get_company_culture_report(company_name)
        
        if culture.get("success") != False:
            report += f"- Reviews Analyzed: {culture['total_reviews_analyzed']}\n"
            report += f"- Current Employees: {culture['current_employees']}\n"
            report += f"- Former Employees: {culture['former_employees']}\n\n"
            
            report += "### Ratings Breakdown:\n"
            for category, rating in culture["average_ratings"].items():
                report += f"- {category.replace('_', ' ').title()}: {rating}\n"
            
            if culture["top_pros"]:
                report += "\n### Top Pros:\n"
                for pro in culture["top_pros"]:
                    report += f"- {pro['item'].title()} (mentioned {pro['count']} times)\n"
            
            if culture["top_cons"]:
                report += "\n### Top Cons:\n"
                for con in culture["top_cons"]:
                    report += f"- {con['item'].title()} (mentioned {con['count']} times)\n"
            
            report += f"\n### Summary:\n{culture['culture_summary']}\n"
        else:
            report += "No review data available\n"
        
        # Benefits
        if company.get("benefits"):
            report += "\n## Benefits & Perks\n"
            for benefit in company["benefits"]:
                report += f"- {benefit}\n"
        
        # Research checklist
        checklist = self.get_research_checklist(company_name)
        if checklist.get("success") != False:
            report += f"\n## Research Progress: {checklist['progress']}\n"
            if checklist.get("next_steps"):
                report += "\n### Next Steps:\n"
                for step in checklist["next_steps"]:
                    report += f"- [ ] {step.replace('_', ' ').title()}\n"
        
        report += f"\n---\nLast Updated: {company['last_updated'][:10]}\n"
        
        return report
    
    def _format_difficulty_dist(self, dist: Dict) -> str:
        """Format difficulty distribution"""
        total = sum(dist.values())
        if total == 0:
            return "Unknown"
        
        parts = []
        for level, count in dist.items():
            if count > 0:
                pct = count / total * 100
                parts.append(f"{level.title()} {pct:.0f}%")
        
        return ", ".join(parts)
    
    def get_daily_research_tasks(self) -> Dict:
        """Get prioritized research tasks for today"""
        
        tasks = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "follow_ups": []
        }
        
        # Get queued and in-progress items
        active_research = [
            item for item in self.research_queue 
            if item["status"] in ["queued", "in_progress"]
        ]
        
        for item in active_research:
            checklist = item["research_checklist"]
            incomplete_items = [k for k, v in checklist.items() if not v]
            
            task = {
                "company_name": item["company_name"],
                "reason": item["reason"],
                "specific_role": item.get("specific_role"),
                "incomplete_items": incomplete_items,
                "progress": f"{sum(1 for v in checklist.values() if v)}/{len(checklist)}"
            }
            
            if item["priority"] == "high":
                tasks["high_priority"].append(task)
            elif item["priority"] == "medium":
                tasks["medium_priority"].append(task)
            else:
                tasks["low_priority"].append(task)
        
        # Get companies needing follow-up (data older than 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        for company in self.companies:
            if company["last_updated"] < thirty_days_ago:
                tasks["follow_ups"].append({
                    "company_name": company["company_name"],
                    "last_updated": company["last_updated"][:10],
                    "action": "Refresh salary/interview data"
                })
        
        return tasks


if __name__ == "__main__":
    # Example usage
    glassdoor = GlassdoorAutomation()
    
    # Add company to research
    result = glassdoor.add_company_to_research(
        company_name="OpenAI",
        priority="high",
        reason="job_application",
        specific_role="Machine Learning Engineer"
    )
    print(json.dumps(result, indent=2))
    
    # Log company overview
    glassdoor.log_company_data(
        company_name="OpenAI",
        data_type="overview",
        data={
            "industry": "Artificial Intelligence",
            "size": "500-1000",
            "founded": "2015",
            "headquarters": "San Francisco, CA",
            "overall_rating": 4.5,
            "ceo_approval": 95,
            "recommend_to_friend": 87,
            "website": "openai.com"
        }
    )
    
    # Log salary data
    glassdoor.log_company_data(
        company_name="OpenAI",
        data_type="salary",
        data={
            "role": "Machine Learning Engineer",
            "base_salary_min": 180000,
            "base_salary_max": 250000,
            "base_salary_avg": 215000,
            "total_comp_min": 250000,
            "total_comp_max": 400000,
            "total_comp_avg": 325000,
            "bonus": 50000,
            "stock": 60000,
            "location": "San Francisco, CA",
            "experience_level": "Mid-Senior",
            "data_points": 15
        }
    )
    
    # Log interview data
    glassdoor.log_company_data(
        company_name="OpenAI",
        data_type="interview",
        data={
            "role": "Machine Learning Engineer",
            "overall_experience": "positive",
            "difficulty": "hard",
            "process_length": 21,
            "interview_rounds": [
                "recruiter_call",
                "technical_screen",
                "coding_interview",
                "system_design",
                "behavioral",
                "team_fit"
            ],
            "questions_asked": [
                "Explain transformer architecture in detail",
                "Design a recommendation system for 100M users",
                "How would you improve GPT's training efficiency?",
                "Implement attention mechanism from scratch",
                "Discuss a challenging ML project you've worked on"
            ],
            "offer_received": True
        }
    )
    
    # Log review data
    glassdoor.log_company_data(
        company_name="OpenAI",
        data_type="review",
        data={
            "role": "Machine Learning Engineer",
            "rating": 4.5,
            "work_life_balance": 3.5,
            "culture_values": 5.0,
            "career_opportunities": 4.5,
            "comp_benefits": 4.8,
            "senior_management": 4.7,
            "pros": [
                "Cutting-edge AI research",
                "Brilliant colleagues",
                "Impactful work",
                "Great compensation",
                "Strong mission"
            ],
            "cons": [
                "Fast-paced environment",
                "High expectations",
                "Work-life balance can be challenging"
            ],
            "advice_to_management": "Continue fostering innovation while maintaining work-life balance",
            "employment_status": "current"
        }
    )
    
    # Get salary insights
    salary_insights = glassdoor.get_salary_insights("OpenAI", "Machine Learning Engineer")
    print(json.dumps(salary_insights, indent=2))
    
    # Get interview prep
    interview_prep = glassdoor.get_interview_prep("OpenAI", "Machine Learning Engineer")
    print(json.dumps(interview_prep, indent=2))
    
    # Get culture report
    culture_report = glassdoor.get_company_culture_report("OpenAI")
    print(json.dumps(culture_report, indent=2))
    
    # Get research checklist
    checklist = glassdoor.get_research_checklist("OpenAI")
    print(json.dumps(checklist, indent=2))
    
    # Generate full report
    full_report = glassdoor.generate_full_research_report("OpenAI")
    print(full_report)
    
    # Get daily tasks
    daily_tasks = glassdoor.get_daily_research_tasks()
    print(json.dumps(daily_tasks, indent=2))
