#!/usr/bin/env python3
"""
Job Search Automation - Live Dashboard
Real-time monitoring and control for your job search pipeline
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
import argparse


class JobSearchDashboard:
    def __init__(self):
        self.data_files = {
            'applications': 'applications.json',
            'discovered': 'discovered_jobs.json',
            'matched': 'matched_jobs.json',
            'network': 'network_contacts.json',
            'resume_versions': 'resume_versions.json',
            'activity': 'linkedin_activity.json',
            'deadlines': 'application_deadlines.json'
        }
        self.data = {}
        self.load_all_data()
    
    def load_all_data(self):
        """Load all JSON data files"""
        for key, filename in self.data_files.items():
            try:
                with open(filename, 'r') as f:
                    self.data[key] = json.load(f)
            except FileNotFoundError:
                self.data[key] = [] if key != 'resume_versions' else {}
            except json.JSONDecodeError:
                print(f"⚠️  Warning: {filename} is corrupted")
                self.data[key] = []
    
    def show_overview(self):
        """Display system overview"""
        apps = self.data['applications']
        discovered = self.data['discovered']
        matched = self.data['matched']
        network = self.data['network']
        
        print("\n" + "="*60)
        print("🎯 JOB SEARCH AUTOMATION - SYSTEM OVERVIEW")
        print("="*60)
        
        # Pipeline Status
        print("\n📊 PIPELINE STATUS")
        print(f"   Jobs Discovered: {len(discovered)}")
        print(f"   Jobs Matched: {len(matched)}")
        print(f"   Applications Sent: {len(apps)}")
        print(f"   Network Contacts: {len(network)}")
        
        # Today's Activity
        today = datetime.now().date()
        today_apps = [a for a in apps 
                     if datetime.fromisoformat(a.get('applied_date', '2000-01-01')).date() == today]
        
        print(f"\n📅 TODAY'S ACTIVITY")
        print(f"   Applications: {len(today_apps)}/50")
        print(f"   Remaining: {max(0, 50 - len(today_apps))}")
        
        # Conversion Metrics
        if apps:
            interviews = len([a for a in apps if a.get('status') == 'interview'])
            offers = len([a for a in apps if a.get('status') == 'offer'])
            response_rate = len([a for a in apps if a.get('status') != 'pending']) / len(apps) * 100
            
            print(f"\n📈 CONVERSION RATES")
            print(f"   Response Rate: {response_rate:.1f}%")
            print(f"   Interview Rate: {interviews/len(apps)*100:.1f}%")
            print(f"   Offer Rate: {offers/len(apps)*100:.1f}%")
        
        # Status Breakdown
        if apps:
            status_counts = Counter(a.get('status', 'unknown') for a in apps)
            print(f"\n🔍 STATUS BREAKDOWN")
            for status, count in status_counts.most_common():
                print(f"   {status.title()}: {count}")
        
        print("\n" + "="*60 + "\n")
    
    def show_top_matches(self, limit=10):
        """Display top job matches"""
        matched = sorted(self.data['matched'], 
                        key=lambda x: x.get('match_score', 0), 
                        reverse=True)[:limit]
        
        print("\n" + "="*60)
        print(f"🎯 TOP {limit} JOB MATCHES")
        print("="*60)
        
        for i, job in enumerate(matched, 1):
            print(f"\n{i}. {job.get('company', 'Unknown')} - {job.get('title', 'Unknown')}")
            print(f"   Match Score: {job.get('match_score', 0)}/100 ⭐")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Salary: {job.get('salary', 'Not specified')}")
            
            reasons = job.get('match_reasons', [])
            if reasons:
                print(f"   Why it matches:")
                for reason in reasons[:3]:
                    print(f"      • {reason}")
            
            applied = any(a.get('job_id') == job.get('job_id') 
                         for a in self.data['applications'])
            print(f"   Status: {'✅ Applied' if applied else '⏳ Pending'}")
        
        print("\n" + "="*60 + "\n")
    
    def show_networking_opportunities(self):
        """Display networking insights"""
        network = self.data['network']
        matched = self.data['matched']
        
        print("\n" + "="*60)
        print("🤝 NETWORKING OPPORTUNITIES")
        print("="*60)
        
        # Companies where we have connections
        company_connections = defaultdict(list)
        for contact in network:
            company = contact.get('company')
            if company and contact.get('can_refer'):
                company_connections[company].append(contact)
        
        # Match with target companies
        target_companies = set(j.get('company') for j in matched[:20])
        
        print("\n📍 TARGET COMPANIES WITH CONNECTIONS:")
        opportunities = 0
        for company in target_companies:
            if company in company_connections:
                contacts = company_connections[company]
                print(f"\n   {company}:")
                for contact in contacts[:3]:
                    print(f"      • {contact.get('name')} - {contact.get('position')}")
                    if contact.get('connection_level') == '2nd':
                        mutual = contact.get('mutual_connections', 0)
                        print(f"        (2nd degree, {mutual} mutual connections)")
                opportunities += 1
        
        if opportunities == 0:
            print("\n   ⚠️  No direct connections at target companies")
            print("   💡 Tip: Run networking mode to discover connections")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total contacts: {len(network)}")
        print(f"   Can refer: {len([c for c in network if c.get('can_refer')])}")
        print(f"   Referral opportunities: {opportunities}")
        
        print("\n" + "="*60 + "\n")
    
    def show_timeline(self, days=7):
        """Show application timeline"""
        apps = self.data['applications']
        
        print("\n" + "="*60)
        print(f"📅 APPLICATION TIMELINE (Last {days} days)")
        print("="*60)
        
        # Group by date
        timeline = defaultdict(list)
        cutoff = datetime.now() - timedelta(days=days)
        
        for app in apps:
            try:
                app_date = datetime.fromisoformat(app.get('applied_date', ''))
                if app_date >= cutoff:
                    date_str = app_date.strftime('%Y-%m-%d')
                    timeline[date_str].append(app)
            except:
                continue
        
        # Display timeline
        for date_str in sorted(timeline.keys(), reverse=True):
            apps_on_date = timeline[date_str]
            print(f"\n📆 {date_str} ({len(apps_on_date)} applications)")
            for app in apps_on_date[:5]:  # Show max 5 per day
                company = app.get('company', 'Unknown')
                title = app.get('title', 'Unknown')[:40]
                status = app.get('status', 'pending')
                print(f"   • {company} - {title} [{status}]")
            if len(apps_on_date) > 5:
                print(f"   ... and {len(apps_on_date) - 5} more")
        
        print("\n" + "="*60 + "\n")
    
    def show_upcoming_followups(self):
        """Show follow-up reminders"""
        deadlines = self.data['deadlines']
        
        print("\n" + "="*60)
        print("⏰ UPCOMING FOLLOW-UPS")
        print("="*60)
        
        # Sort by follow-up date
        today = datetime.now()
        upcoming = []
        
        for deadline in deadlines:
            try:
                followup_date = datetime.fromisoformat(deadline.get('follow_up_date', ''))
                days_until = (followup_date - today).days
                if -2 <= days_until <= 7:  # Show overdue up to 2 days and upcoming 7 days
                    deadline['days_until'] = days_until
                    upcoming.append(deadline)
            except:
                continue
        
        upcoming.sort(key=lambda x: x['days_until'])
        
        if not upcoming:
            print("\n   ✅ No upcoming follow-ups")
        else:
            for item in upcoming[:10]:
                company = item.get('company', 'Unknown')
                title = item.get('title', 'Unknown')[:40]
                days = item['days_until']
                
                if days < 0:
                    status = f"⚠️  OVERDUE by {abs(days)} days"
                elif days == 0:
                    status = "🔥 TODAY"
                elif days == 1:
                    status = "📌 TOMORROW"
                else:
                    status = f"📅 In {days} days"
                
                print(f"\n   {status}")
                print(f"   {company} - {title}")
        
        print("\n" + "="*60 + "\n")
    
    def show_performance_analysis(self):
        """Analyze what's working"""
        apps = self.data['applications']
        
        if not apps:
            print("\n⚠️  No application data yet\n")
            return
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE ANALYSIS")
        print("="*60)
        
        # Best job boards
        print("\n🎯 BEST PERFORMING JOB BOARDS:")
        source_performance = defaultdict(lambda: {'total': 0, 'interviews': 0, 'offers': 0})
        
        for app in apps:
            source = app.get('source', 'unknown')
            status = app.get('status', 'pending')
            
            source_performance[source]['total'] += 1
            if status == 'interview':
                source_performance[source]['interviews'] += 1
            if status == 'offer':
                source_performance[source]['offers'] += 1
        
        for source, stats in sorted(source_performance.items(), 
                                    key=lambda x: x[1]['interviews'], 
                                    reverse=True):
            total = stats['total']
            interviews = stats['interviews']
            offers = stats['offers']
            rate = interviews/total*100 if total > 0 else 0
            
            print(f"   {source}:")
            print(f"      Applications: {total}")
            print(f"      Interviews: {interviews} ({rate:.1f}%)")
            print(f"      Offers: {offers}")
        
        # Best application times
        print("\n⏰ BEST APPLICATION TIMES:")
        time_performance = defaultdict(lambda: {'total': 0, 'responses': 0})
        
        for app in apps:
            try:
                app_datetime = datetime.fromisoformat(app.get('applied_date', ''))
                hour = app_datetime.hour
                time_slot = f"{hour:02d}:00-{hour+1:02d}:00"
                
                time_performance[time_slot]['total'] += 1
                if app.get('status') != 'pending':
                    time_performance[time_slot]['responses'] += 1
            except:
                continue
        
        for time_slot, stats in sorted(time_performance.items(), 
                                       key=lambda x: x[1]['responses']/max(1,x[1]['total']), 
                                       reverse=True)[:5]:
            total = stats['total']
            responses = stats['responses']
            rate = responses/total*100 if total > 0 else 0
            print(f"   {time_slot}: {responses}/{total} responses ({rate:.1f}%)")
        
        # Top companies
        print("\n🏢 MOST APPLIED COMPANIES:")
        company_counts = Counter(app.get('company', 'Unknown') for app in apps)
        for company, count in company_counts.most_common(10):
            print(f"   {company}: {count} applications")
        
        print("\n" + "="*60 + "\n")
    
    def show_health_check(self):
        """System health check"""
        print("\n" + "="*60)
        print("🏥 SYSTEM HEALTH CHECK")
        print("="*60)
        
        issues = []
        warnings = []
        
        # Check data files
        print("\n📂 DATA FILES:")
        for key, filename in self.data_files.items():
            path = Path(filename)
            if path.exists():
                size = path.stat().st_size
                print(f"   ✅ {filename} ({size} bytes)")
                
                # Check for issues
                if size == 0:
                    warnings.append(f"{filename} is empty")
                elif size > 10_000_000:  # 10MB
                    warnings.append(f"{filename} is very large ({size/1_000_000:.1f}MB)")
            else:
                print(f"   ❌ {filename} MISSING")
                issues.append(f"Missing file: {filename}")
        
        # Check application limits
        today = datetime.now().date()
        today_apps = [a for a in self.data['applications'] 
                     if datetime.fromisoformat(a.get('applied_date', '2000-01-01')).date() == today]
        
        print(f"\n📊 APPLICATION LIMITS:")
        print(f"   Today's applications: {len(today_apps)}/50")
        if len(today_apps) >= 50:
            warnings.append("Daily application limit reached")
        elif len(today_apps) >= 40:
            warnings.append(f"Approaching daily limit ({len(today_apps)}/50)")
        
        # Check for stale data
        print(f"\n🕐 DATA FRESHNESS:")
        if self.data['discovered']:
            latest_discovery = max(
                datetime.fromisoformat(j.get('discovered_date', '2000-01-01'))
                for j in self.data['discovered']
                if j.get('discovered_date')
            )
            hours_old = (datetime.now() - latest_discovery).total_seconds() / 3600
            print(f"   Last job discovery: {hours_old:.1f} hours ago")
            
            if hours_old > 24:
                warnings.append(f"No new jobs discovered in {hours_old:.1f} hours")
        
        # Summary
        print(f"\n🎯 SUMMARY:")
        if issues:
            print(f"   ❌ {len(issues)} critical issues")
            for issue in issues:
                print(f"      • {issue}")
        else:
            print(f"   ✅ No critical issues")
        
        if warnings:
            print(f"   ⚠️  {len(warnings)} warnings")
            for warning in warnings:
                print(f"      • {warning}")
        else:
            print(f"   ✅ No warnings")
        
        if not issues and not warnings:
            print(f"\n   🎉 System is healthy!")
        
        print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Job Search Automation Dashboard')
    parser.add_argument('--overview', action='store_true', help='Show system overview')
    parser.add_argument('--matches', type=int, default=10, help='Show top N matches')
    parser.add_argument('--networking', action='store_true', help='Show networking opportunities')
    parser.add_argument('--timeline', type=int, help='Show timeline for N days')
    parser.add_argument('--followups', action='store_true', help='Show upcoming follow-ups')
    parser.add_argument('--performance', action='store_true', help='Show performance analysis')
    parser.add_argument('--health', action='store_true', help='Run health check')
    parser.add_argument('--all', action='store_true', help='Show all reports')
    
    args = parser.parse_args()
    
    dashboard = JobSearchDashboard()
    
    # If no specific flag, show overview
    if not any([args.overview, args.networking, args.timeline, 
                args.followups, args.performance, args.health, args.all]):
        args.overview = True
    
    if args.all:
        dashboard.show_overview()
        dashboard.show_top_matches(args.matches)
        dashboard.show_networking_opportunities()
        dashboard.show_timeline(7)
        dashboard.show_upcoming_followups()
        dashboard.show_performance_analysis()
        dashboard.show_health_check()
    else:
        if args.overview:
            dashboard.show_overview()
        if args.matches or not args.all:
            dashboard.show_top_matches(args.matches)
        if args.networking:
            dashboard.show_networking_opportunities()
        if args.timeline:
            dashboard.show_timeline(args.timeline)
        if args.followups:
            dashboard.show_upcoming_followups()
        if args.performance:
            dashboard.show_performance_analysis()
        if args.health:
            dashboard.show_health_check()


if __name__ == '__main__':
    main()
