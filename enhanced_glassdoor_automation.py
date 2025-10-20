#!/usr/bin/env python3
"""
Enhanced features for Glassdoor Research Automation
Export, Search, and Filter capabilities
"""

import csv
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime

class GlassdoorEnhanced:
    """Enhanced export and search capabilities"""
    
    def __init__(self, glassdoor_instance):
        self.gd = glassdoor_instance
        self.export_dir = self.gd.data_dir / "exports"
        self.export_dir.mkdir(exist_ok=True)
    
    # ==================== EXPORT FUNCTIONALITY ====================
    
    def export_companies_csv(self, filename: str = None) -> str:
        """Export all companies to CSV"""
        if not filename:
            filename = f"companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        
        if not self.gd.companies:
            return "No companies to export"
        
        # Determine all possible fields
        fieldnames = [
            'id', 'company_name', 'overall_rating', 'ceo_approval', 
            'recommend_to_friend', 'industry', 'size', 'founded', 
            'headquarters', 'website', 'last_updated', 'research_completed'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.gd.companies)
        
        return f"Exported {len(self.gd.companies)} companies to {filepath}"
    
    def export_salaries_csv(self, company_name: str = None, filename: str = None) -> str:
        """Export salary data to CSV"""
        if not filename:
            suffix = f"_{company_name.replace(' ', '_')}" if company_name else ""
            filename = f"salaries{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        
        # Filter salaries if company specified
        salaries = self.gd.salaries
        if company_name:
            salaries = [s for s in salaries if s['company_name'].lower() == company_name.lower()]
        
        if not salaries:
            return "No salary data to export"
        
        fieldnames = [
            'company_name', 'role', 'base_salary_avg', 'total_comp_avg',
            'bonus', 'stock', 'location', 'experience_level', 'data_points'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(salaries)
        
        return f"Exported {len(salaries)} salary records to {filepath}"
    
    def export_interviews_csv(self, company_name: str = None, filename: str = None) -> str:
        """Export interview data to CSV"""
        if not filename:
            suffix = f"_{company_name.replace(' ', '_')}" if company_name else ""
            filename = f"interviews{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        
        interviews = self.gd.interviews
        if company_name:
            interviews = [i for i in interviews if i['company_name'].lower() == company_name.lower()]
        
        if not interviews:
            return "No interview data to export"
        
        # Flatten data for CSV
        flattened = []
        for interview in interviews:
            flat = {
                'company_name': interview['company_name'],
                'role': interview['role'],
                'overall_experience': interview.get('overall_experience'),
                'difficulty': interview.get('difficulty'),
                'process_length': interview.get('process_length'),
                'offer_received': interview.get('offer_received'),
                'interview_rounds': ', '.join(interview.get('interview_rounds', [])),
                'questions_asked': ' | '.join(interview.get('questions_asked', []))
            }
            flattened.append(flat)
        
        fieldnames = list(flattened[0].keys()) if flattened else []
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened)
        
        return f"Exported {len(flattened)} interview records to {filepath}"
    
    def export_full_report_markdown(self, company_name: str, filename: str = None) -> str:
        """Export full company report as Markdown"""
        if not filename:
            filename = f"{company_name.replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d')}.md"
        
        filepath = self.export_dir / filename
        
        report = self.gd.generate_full_research_report(company_name)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return f"Exported report to {filepath}"
    
    def export_comparison_csv(self, company_names: List[str], filename: str = None) -> str:
        """Export comparison of multiple companies to CSV"""
        if not filename:
            filename = f"company_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        
        comparison_data = []
        
        for company_name in company_names:
            company = self.gd._get_company(company_name)
            if not company:
                continue
            
            # Get salary insights
            salary_insights = self.gd.get_salary_insights(company_name)
            avg_comp = None
            if isinstance(salary_insights, dict) and salary_insights.get('total_compensation'):
                avg_comp = salary_insights['total_compensation'].get('average')
            
            # Get culture report
            culture = self.gd.get_company_culture_report(company_name)
            
            row = {
                'company_name': company_name,
                'overall_rating': company.get('overall_rating'),
                'ceo_approval': company.get('ceo_approval'),
                'recommend_to_friend': company.get('recommend_to_friend'),
                'industry': company.get('industry'),
                'size': company.get('size'),
                'avg_total_comp': avg_comp,
                'total_reviews': culture.get('total_reviews_analyzed', 0) if isinstance(culture, dict) else 0,
                'work_life_balance': culture.get('average_ratings', {}).get('work_life_balance', 'N/A') if isinstance(culture, dict) else 'N/A',
                'culture_values': culture.get('average_ratings', {}).get('culture_values', 'N/A') if isinstance(culture, dict) else 'N/A',
                'career_opportunities': culture.get('average_ratings', {}).get('career_opportunities', 'N/A') if isinstance(culture, dict) else 'N/A'
            }
            comparison_data.append(row)
        
        if not comparison_data:
            return "No companies found for comparison"
        
        fieldnames = list(comparison_data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comparison_data)
        
        return f"Exported comparison of {len(comparison_data)} companies to {filepath}"
    
    def export_all_data(self) -> Dict[str, str]:
        """Export all data to multiple files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        results = {
            'companies': self.export_companies_csv(f"companies_{timestamp}.csv"),
            'salaries': self.export_salaries_csv(filename=f"salaries_{timestamp}.csv"),
            'interviews': self.export_interviews_csv(filename=f"interviews_{timestamp}.csv"),
        }
        
        # Export individual company reports
        for company in self.gd.companies:
            company_name = company['company_name']
            results[f'report_{company_name}'] = self.export_full_report_markdown(company_name)
        
        return results
    
    # ==================== SEARCH & FILTER FUNCTIONALITY ====================
    
    def search_companies(self, 
                        name: str = None,
                        industry: str = None,
                        min_rating: float = None,
                        max_rating: float = None,
                        min_size: int = None,
                        max_size: int = None,
                        location: str = None) -> List[Dict]:
        """Search and filter companies"""
        
        results = self.gd.companies.copy()
        
        # Filter by name
        if name:
            results = [c for c in results if name.lower() in c['company_name'].lower()]
        
        # Filter by industry
        if industry:
            results = [c for c in results if c.get('industry') and industry.lower() in c['industry'].lower()]
        
        # Filter by rating
        if min_rating is not None:
            results = [c for c in results if c.get('overall_rating') and c['overall_rating'] >= min_rating]
        
        if max_rating is not None:
            results = [c for c in results if c.get('overall_rating') and c['overall_rating'] <= max_rating]
        
        # Filter by size
        if min_size is not None or max_size is not None:
            filtered = []
            for c in results:
                if not c.get('size'):
                    continue
                
                size_str = c['size']
                # Parse size ranges like "500-1000" or "10000+"
                try:
                    if '+' in size_str:
                        size_num = int(size_str.replace('+', '').replace(',', ''))
                    elif '-' in size_str:
                        # Take the midpoint
                        parts = size_str.split('-')
                        size_num = (int(parts[0]) + int(parts[1])) / 2
                    else:
                        size_num = int(size_str.replace(',', ''))
                    
                    if min_size and size_num < min_size:
                        continue
                    if max_size and size_num > max_size:
                        continue
                    
                    filtered.append(c)
                except:
                    continue
            
            results = filtered
        
        # Filter by location
        if location:
            results = [c for c in results if c.get('headquarters') and location.lower() in c['headquarters'].lower()]
        
        return results
    
    def search_salaries(self,
                       company_name: str = None,
                       role: str = None,
                       min_salary: float = None,
                       max_salary: float = None,
                       location: str = None,
                       experience_level: str = None) -> List[Dict]:
        """Search and filter salary data"""
        
        results = self.gd.salaries.copy()
        
        if company_name:
            results = [s for s in results if company_name.lower() in s['company_name'].lower()]
        
        if role:
            results = [s for s in results if role.lower() in s['role'].lower()]
        
        if min_salary is not None:
            results = [s for s in results if s.get('total_comp_avg') and s['total_comp_avg'] >= min_salary]
        
        if max_salary is not None:
            results = [s for s in results if s.get('total_comp_avg') and s['total_comp_avg'] <= max_salary]
        
        if location:
            results = [s for s in results if s.get('location') and location.lower() in s['location'].lower()]
        
        if experience_level:
            results = [s for s in results if s.get('experience_level') and experience_level.lower() in s['experience_level'].lower()]
        
        return results
    
    def search_interviews(self,
                         company_name: str = None,
                         role: str = None,
                         difficulty: str = None,
                         experience: str = None,
                         offer_received: bool = None) -> List[Dict]:
        """Search and filter interview data"""
        
        results = self.gd.interviews.copy()
        
        if company_name:
            results = [i for i in results if company_name.lower() in i['company_name'].lower()]
        
        if role:
            results = [i for i in results if role.lower() in i['role'].lower()]
        
        if difficulty:
            results = [i for i in results if i.get('difficulty') == difficulty.lower()]
        
        if experience:
            results = [i for i in results if i.get('overall_experience') == experience.lower()]
        
        if offer_received is not None:
            results = [i for i in results if i.get('offer_received') == offer_received]
        
        return results
    
    def find_best_companies(self, 
                           criteria: str = "overall_rating",
                           min_reviews: int = 0,
                           limit: int = 10) -> List[Dict]:
        """Find top companies based on criteria"""
        
        valid_criteria = [
            'overall_rating', 'ceo_approval', 'recommend_to_friend',
            'work_life_balance', 'culture_values', 'career_opportunities',
            'comp_benefits', 'senior_management'
        ]
        
        if criteria not in valid_criteria:
            return []
        
        ranked = []
        
        for company in self.gd.companies:
            # Get review count
            company_reviews = [r for r in self.gd.reviews if r['company_name'] == company['company_name']]
            
            if len(company_reviews) < min_reviews:
                continue
            
            score = None
            
            if criteria in ['overall_rating', 'ceo_approval', 'recommend_to_friend']:
                score = company.get(criteria)
            else:
                # Calculate from reviews
                scores = [r.get(criteria, 0) for r in company_reviews if r.get(criteria)]
                if scores:
                    import statistics
                    score = statistics.mean(scores)
            
            if score:
                ranked.append({
                    'company_name': company['company_name'],
                    'score': score,
                    'review_count': len(company_reviews),
                    'criteria': criteria
                })
        
        # Sort by score
        ranked.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked[:limit]
    
    def find_high_paying_roles(self, 
                              role_keyword: str = None,
                              min_compensation: float = None,
                              limit: int = 10) -> List[Dict]:
        """Find highest paying roles"""
        
        salaries = self.gd.salaries.copy()
        
        # Filter by role keyword
        if role_keyword:
            salaries = [s for s in salaries if role_keyword.lower() in s['role'].lower()]
        
        # Filter by minimum compensation
        if min_compensation:
            salaries = [s for s in salaries if s.get('total_comp_avg') and s['total_comp_avg'] >= min_compensation]
        
        # Sort by total compensation
        salaries.sort(key=lambda x: x.get('total_comp_avg', 0), reverse=True)
        
        return salaries[:limit]
    
    def generate_search_report(self, search_results: List[Dict], search_type: str) -> str:
        """Generate formatted report from search results"""
        
        if not search_results:
            return "No results found"
        
        report = f"\n{'='*60}\n"
        report += f"Search Results: {search_type}\n"
        report += f"Found {len(search_results)} results\n"
        report += f"{'='*60}\n\n"
        
        if search_type == "companies":
            for i, company in enumerate(search_results, 1):
                report += f"{i}. {company['company_name']}\n"
                if company.get('overall_rating'):
                    report += f"   Rating: {company['overall_rating']}/5.0\n"
                if company.get('industry'):
                    report += f"   Industry: {company['industry']}\n"
                if company.get('headquarters'):
                    report += f"   Location: {company['headquarters']}\n"
                report += "\n"
        
        elif search_type == "salaries":
            for i, salary in enumerate(search_results, 1):
                report += f"{i}. {salary['company_name']} - {salary['role']}\n"
                if salary.get('total_comp_avg'):
                    report += f"   Total Comp: ${salary['total_comp_avg']:,.0f}\n"
                if salary.get('base_salary_avg'):
                    report += f"   Base Salary: ${salary['base_salary_avg']:,.0f}\n"
                if salary.get('location'):
                    report += f"   Location: {salary['location']}\n"
                report += "\n"
        
        elif search_type == "interviews":
            for i, interview in enumerate(search_results, 1):
                report += f"{i}. {interview['company_name']} - {interview['role']}\n"
                if interview.get('difficulty'):
                    report += f"   Difficulty: {interview['difficulty']}\n"
                if interview.get('overall_experience'):
                    report += f"   Experience: {interview['overall_experience']}\n"
                if interview.get('offer_received') is not None:
                    report += f"   Offer: {'Yes' if interview['offer_received'] else 'No'}\n"
                report += "\n"
        
        return report


# Example usage functions
def demo_export_features():
    """Demonstrate export functionality"""
    from glassdoor_automation import GlassdoorAutomation
    
    gd = GlassdoorAutomation()
    enhanced = GlassdoorEnhanced(gd)
    
    print("=== Export Examples ===\n")
    
    # Export all companies
    print(enhanced.export_companies_csv())
    
    # Export salaries for specific company
    print(enhanced.export_salaries_csv("OpenAI"))
    
    # Export company comparison
    companies = ["OpenAI", "Google", "Microsoft"]
    print(enhanced.export_comparison_csv(companies))
    
    # Export all data
    results = enhanced.export_all_data()
    print("\nExported all data:")
    for key, result in results.items():
        print(f"  {key}: {result}")


def demo_search_features():
    """Demonstrate search functionality"""
    from glassdoor_automation import GlassdoorAutomation
    
    gd = GlassdoorAutomation()
    enhanced = GlassdoorEnhanced(gd)
    
    print("\n=== Search Examples ===\n")
    
    # Search companies by rating
    results = enhanced.search_companies(min_rating=4.0, industry="Technology")
    print(enhanced.generate_search_report(results, "companies"))
    
    # Find high paying roles
    high_paying = enhanced.find_high_paying_roles(role_keyword="Engineer", limit=5)
    print(enhanced.generate_search_report(high_paying, "salaries"))
    
    # Search interviews by difficulty
    hard_interviews = enhanced.search_interviews(difficulty="hard")
    print(enhanced.generate_search_report(hard_interviews, "interviews"))
    
    # Find best companies
    best = enhanced.find_best_companies(criteria="work_life_balance", min_reviews=5)
    print("\nTop companies by work-life balance:")
    for i, company in enumerate(best, 1):
        print(f"{i}. {company['company_name']}: {company['score']:.1f}/5.0 ({company['review_count']} reviews)")


if __name__ == "__main__":
    demo_export_features()
    demo_search_features()
