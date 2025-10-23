#!/usr/bin/env python3
"""
Follow-Up Reminder System
=========================
Automated reminder management with:
- Email templates for follow-ups
- Smart scheduling
- Priority-based alerts
- Snooze functionality
- Batch reminder processing
- Integration with calendar systems
"""

import json
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import argparse
from collections import defaultdict

# Import tracker
sys.path.insert(0, str(Path(__file__).parent))
try:
    from application_tracker_plus import ApplicationTracker
except ImportError:
    print("❌ Cannot import ApplicationTracker")
    sys.exit(1)


class FollowUpManager:
    """Manage follow-ups and reminders for job applications"""
    
    # Follow-up templates
    FOLLOW_UP_TEMPLATES = {
        'initial_submission': {
            'subject': 'Following up on {position} application',
            'body': """Dear Hiring Manager,

I hope this email finds you well. I recently applied for the {position} role at {company} and wanted to follow up on my application.

I'm very excited about the opportunity to contribute to {company}'s {company_strength}. With my experience in {key_skills}, I believe I would be a strong addition to your team.

I'd welcome the opportunity to discuss how my background aligns with your needs. Please let me know if you need any additional information from me.

Thank you for your consideration.

Best regards,
{your_name}"""
        },
        
        'post_interview': {
            'subject': 'Thank you - {position} interview',
            'body': """Dear {interviewer_name},

Thank you for taking the time to meet with me {interview_date} to discuss the {position} role at {company}.

I enjoyed learning more about {specific_topic} and the team's approach to {interesting_point}. Our conversation reinforced my enthusiasm for the position and {company}'s mission.

I'm confident that my experience with {relevant_skill} would enable me to contribute effectively to {specific_project}.

Please don't hesitate to reach out if you need any additional information. I look forward to hearing about next steps.

Best regards,
{your_name}"""
        },
        
        'second_follow_up': {
            'subject': 'Re: {position} application',
            'body': """Dear Hiring Manager,

I wanted to reach out once more regarding my application for the {position} role at {company}.

I remain very interested in this opportunity and would appreciate any update on the hiring timeline. I understand you're likely reviewing many qualified candidates.

If there's any additional information I can provide to support my application, please let me know.

Thank you for your time and consideration.

Best regards,
{your_name}"""
        },
        
        'offer_acceptance': {
            'subject': 'Accepting {position} offer - {your_name}',
            'body': """Dear {hiring_manager},

I'm delighted to formally accept your offer for the {position} role at {company}.

As discussed, I will:
- Start date: {start_date}
- Salary: {salary}
- Benefits: {benefits}

I'm excited to join the team and contribute to {company}'s success. Please let me know the next steps and any paperwork I should complete.

Thank you again for this wonderful opportunity.

Best regards,
{your_name}"""
        },
        
        'offer_decline': {
            'subject': 'Re: {position} offer',
            'body': """Dear {hiring_manager},

Thank you very much for offering me the {position} role at {company}. I sincerely appreciate the time and consideration you've given me throughout this process.

After careful consideration, I've decided to pursue another opportunity that aligns more closely with my current career goals. This was a difficult decision, as I was impressed by {company} and the team.

I wish you and {company} continued success, and I hope our paths may cross again in the future.

Best regards,
{your_name}"""
        }
    }
    
    # Reminder priority thresholds (days)
    PRIORITY_THRESHOLDS = {
        'critical': 0,  # Due today or overdue
        'high': 1,      # Due tomorrow
        'medium': 3,    # Due within 3 days
        'low': 7        # Due within a week
    }
    
    def __init__(self, data_dir: str = 'job_search'):
        self.tracker = ApplicationTracker(data_dir)
        self.data_dir = Path(data_dir)
        self.reminders_file = self.data_dir / 'reminders_config.json'
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load reminder configuration"""
        if self.reminders_file.exists():
            with open(self.reminders_file) as f:
                return json.load(f)
        
        # Default config
        return {
            'email_enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email_from': '',
            'email_password': '',
            'notification_methods': ['console'],
            'default_snooze_days': 2,
            'auto_reminders': True
        }
    
    def _save_config(self):
        """Save reminder configuration"""
        with open(self.reminders_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_all_reminders(self) -> List[Dict]:
        """Get all reminders with metadata"""
        all_reminders = []
        
        for app in self.tracker.applications:
            for reminder in app.get('reminders', []):
                if not reminder.get('completed'):
                    all_reminders.append({
                        'job_id': app['id'],
                        'company': app['company'],
                        'position': app['position'],
                        'status': app['status'],
                        'reminder': reminder,
                        'application': app
                    })
        
        return all_reminders
    
    def get_due_reminders(self, days_ahead: int = 7) -> List[Dict]:
        """Get reminders due within specified days"""
        cutoff = datetime.now() + timedelta(days=days_ahead)
        all_reminders = self.get_all_reminders()
        
        due_reminders = []
        for item in all_reminders:
            due_date = datetime.fromisoformat(item['reminder']['due_date'])
            if due_date <= cutoff:
                # Calculate priority
                days_until = (due_date - datetime.now()).days
                priority = self._calculate_priority(days_until)
                
                item['days_until'] = days_until
                item['priority'] = priority
                item['overdue'] = days_until < 0
                
                due_reminders.append(item)
        
        # Sort by due date
        due_reminders.sort(key=lambda x: x['reminder']['due_date'])
        
        return due_reminders
    
    def _calculate_priority(self, days_until: int) -> str:
        """Calculate priority based on days until due"""
        if days_until < 0:
            return 'critical'
        
        for priority, threshold in self.PRIORITY_THRESHOLDS.items():
            if days_until <= threshold:
                return priority
        
        return 'low'
    
    def display_reminders(self, reminders: List[Dict]):
        """Display reminders in a formatted table"""
        if not reminders:
            print("\n✅ No reminders due!")
            return
        
        print(f"\n{'='*100}")
        print(f"⏰ FOLLOW-UP REMINDERS ({len(reminders)} items)")
        print(f"{'='*100}")
        
        # Group by priority
        by_priority = defaultdict(list)
        for r in reminders:
            by_priority[r['priority']].append(r)
        
        priority_order = ['critical', 'high', 'medium', 'low']
        priority_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        for priority in priority_order:
            items = by_priority.get(priority, [])
            if not items:
                continue
            
            emoji = priority_emoji[priority]
            print(f"\n{emoji} {priority.upper()} PRIORITY ({len(items)})")
            print("-" * 100)
            
            for item in items:
                reminder = item['reminder']
                app = item['application']
                
                # Format due date
                due_date = datetime.fromisoformat(reminder['due_date'])
                if item['overdue']:
                    due_str = f"OVERDUE by {abs(item['days_until'])} days"
                elif item['days_until'] == 0:
                    due_str = "TODAY"
                elif item['days_until'] == 1:
                    due_str = "TOMORROW"
                else:
                    due_str = f"in {item['days_until']} days"
                
                print(f"\n📌 {item['company']} - {item['position']}")
                print(f"   Job ID: {item['job_id']}")
                print(f"   Status: {item['status']}")
                print(f"   Reminder: {reminder['message']}")
                print(f"   Due: {due_date.strftime('%Y-%m-%d %H:%M')} ({due_str})")
                
                if reminder.get('auto_created'):
                    print(f"   Type: Auto-generated")
    
    def create_follow_up_email(self, 
                               job_id: str, 
                               template_name: str = 'initial_submission',
                               custom_fields: Optional[Dict] = None) -> str:
        """Generate follow-up email from template"""
        app = self.tracker.get_application(job_id)
        if not app:
            raise ValueError(f"Application not found: {job_id}")
        
        template = self.FOLLOW_UP_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Prepare template variables
        profile = self.tracker.profile if hasattr(self.tracker, 'profile') else {}
        
        fields = {
            'company': app['company'],
            'position': app['position'],
            'your_name': profile.get('name', 'Your Name'),
            'company_strength': 'innovative approach',
            'key_skills': ', '.join(app.get('match_reasons', ['relevant skills'])[:3]),
            'interviewer_name': 'Hiring Manager',
            'interview_date': 'recently',
            'specific_topic': 'the role and team',
            'interesting_point': 'solving interesting challenges',
            'relevant_skill': app.get('match_reasons', ['my experience'])[0] if app.get('match_reasons') else 'my experience',
            'specific_project': 'your upcoming projects',
            'hiring_manager': 'Hiring Manager',
            'start_date': 'TBD',
            'salary': 'As discussed',
            'benefits': 'As outlined'
        }
        
        # Override with custom fields
        if custom_fields:
            fields.update(custom_fields)
        
        # Format template
        try:
            subject = template['subject'].format(**fields)
            body = template['body'].format(**fields)
        except KeyError as e:
            print(f"⚠️  Missing field: {e}")
            subject = template['subject']
            body = template['body']
        
        return f"Subject: {subject}\n\n{body}"
    
    def send_follow_up_email(self, 
                            job_id: str,
                            template_name: str,
                            recipient_email: str,
                            custom_fields: Optional[Dict] = None) -> bool:
        """Send follow-up email via SMTP"""
        if not self.config['email_enabled']:
            print("⚠️  Email not enabled in config")
            return False
        
        # Generate email content
        email_content = self.create_follow_up_email(job_id, template_name, custom_fields)
        lines = email_content.split('\n', 2)
        subject = lines[0].replace('Subject: ', '')
        body = lines[2] if len(lines) > 2 else ''
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['email_from']
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()
            
            # Log communication
            app = self.tracker.get_application(job_id)
            self.tracker.add_communication(
                job_id,
                comm_type='email',
                direction='outbound',
                content=f"Follow-up email sent: {template_name}",
                contact_person=recipient_email
            )
            
            print(f"✅ Email sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email send failed: {e}")
            return False
    
    def snooze_reminder(self, job_id: str, reminder_id: str, days: Optional[int] = None) -> bool:
        """Snooze a reminder by specified days"""
        app = self.tracker.get_application(job_id)
        if not app:
            return False
        
        days = days or self.config['default_snooze_days']
        
        for reminder in app.get('reminders', []):
            if reminder['id'] == reminder_id:
                # Update due date
                current_due = datetime.fromisoformat(reminder['due_date'])
                new_due = current_due + timedelta(days=days)
                reminder['due_date'] = new_due.isoformat()
                reminder['snoozed'] = True
                reminder['snooze_count'] = reminder.get('snooze_count', 0) + 1
                
                self.tracker.save_applications()
                print(f"⏰ Reminder snoozed by {days} days (new due: {new_due.strftime('%Y-%m-%d')})")
                return True
        
        return False
    
    def process_reminder(self, reminder_item: Dict, action: str) -> bool:
        """Process a single reminder with specified action"""
        job_id = reminder_item['job_id']
        reminder = reminder_item['reminder']
        reminder_id = reminder['id']
        
        if action == 'complete':
            success = self.tracker.mark_reminder_complete(job_id, reminder_id)
            if success:
                print(f"✅ Reminder marked complete")
            return success
        
        elif action == 'snooze':
            return self.snooze_reminder(job_id, reminder_id)
        
        elif action == 'email':
            # Determine appropriate template
            message = reminder['message'].lower()
            if 'follow-up' in message or 'check' in message:
                template = 'initial_submission'
            elif 'interview' in message:
                template = 'post_interview'
            else:
                template = 'second_follow_up'
            
            print(f"\n📧 Preparing follow-up email...")
            print(f"   Template: {template}")
            
            email = input("   Recipient email (or 'skip'): ").strip()
            if email.lower() != 'skip' and email:
                # Show preview
                preview = self.create_follow_up_email(job_id, template)
                print(f"\n{'='*70}")
                print("EMAIL PREVIEW:")
                print(f"{'='*70}")
                print(preview[:500] + "..." if len(preview) > 500 else preview)
                print(f"{'='*70}")
                
                send = input("\nSend this email? (y/n): ").strip().lower()
                if send == 'y':
                    success = self.send_follow_up_email(job_id, template, email)
                    if success:
                        self.tracker.mark_reminder_complete(job_id, reminder_id)
                    return success
            
            return False
        
        elif action == 'skip':
            print(f"⏭️  Reminder skipped")
            return True
        
        return False
    
    def batch_process_reminders(self, priority_filter: Optional[str] = None):
        """Process multiple reminders interactively"""
        reminders = self.get_due_reminders()
        
        if priority_filter:
            reminders = [r for r in reminders if r['priority'] == priority_filter]
        
        if not reminders:
            print("✅ No reminders to process!")
            return
        
        print(f"\n{'='*100}")
        print(f"🔄 BATCH REMINDER PROCESSING")
        print(f"{'='*100}")
        print(f"Total reminders: {len(reminders)}")
        if priority_filter:
            print(f"Filter: {priority_filter} priority")
        
        processed = 0
        completed = 0
        snoozed = 0
        skipped = 0
        
        for i, reminder_item in enumerate(reminders, 1):
            print(f"\n{'='*100}")
            print(f"[{i}/{len(reminders)}]")
            
            # Display reminder details
            self.display_reminders([reminder_item])
            
            print(f"\n⚡ Actions:")
            print("  1. Mark complete")
            print("  2. Snooze (2 days)")
            print("  3. Send follow-up email")
            print("  4. Skip")
            print("  5. Stop batch processing")
            
            choice = input("\nSelect action (1-5): ").strip()
            
            if choice == '1':
                if self.process_reminder(reminder_item, 'complete'):
                    completed += 1
                    processed += 1
            
            elif choice == '2':
                if self.process_reminder(reminder_item, 'snooze'):
                    snoozed += 1
                    processed += 1
            
            elif choice == '3':
                if self.process_reminder(reminder_item, 'email'):
                    completed += 1
                    processed += 1
            
            elif choice == '4':
                skipped += 1
            
            elif choice == '5':
                print("🛑 Stopping batch processing")
                break
        
        print(f"\n{'='*100}")
        print(f"📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*100}")
        print(f"Processed: {processed}/{len(reminders)}")
        print(f"  Completed: {completed}")
        print(f"  Snoozed: {snoozed}")
        print(f"  Skipped: {skipped}")
    
    def generate_follow_up_report(self, days_ahead: int = 14) -> str:
        """Generate comprehensive follow-up report"""
        reminders = self.get_due_reminders(days_ahead)
        follow_ups_needed = self.tracker.get_follow_up_needed()
        
        report = f"""
{'='*100}
📋 FOLLOW-UP & REMINDER REPORT
{'='*100}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Period: Next {days_ahead} days

{'='*100}
⏰ DUE REMINDERS
{'='*100}
Total: {len(reminders)}

"""
        
        if reminders:
            by_priority = defaultdict(list)
            for r in reminders:
                by_priority[r['priority']].append(r)
            
            for priority in ['critical', 'high', 'medium', 'low']:
                items = by_priority.get(priority, [])
                if items:
                    report += f"\n{priority.upper()}: {len(items)}\n"
                    for item in items[:5]:
                        due = datetime.fromisoformat(item['reminder']['due_date'])
                        report += f"  • {item['company']} - {item['reminder']['message']} (Due: {due.strftime('%Y-%m-%d')})\n"
                    
                    if len(items) > 5:
                        report += f"  ... and {len(items) - 5} more\n"
        
        report += f"""
{'='*100}
📞 FOLLOW-UPS NEEDED
{'='*100}
Total: {len(follow_ups_needed)}

"""
        
        if follow_ups_needed:
            for fu in follow_ups_needed[:10]:
                report += f"""
Company: {fu['company']}
Position: {fu['position']}
Days since submission: {fu['days_since_submission']}
Action: {fu['action']}
Priority: {fu['priority']}
---
"""
        
        # Statistics
        active_apps = self.tracker.get_active_applications()
        submitted_apps = [a for a in active_apps if a['status'] in ['submitted', 'viewed', 'screening']]
        
        report += f"""
{'='*100}
📊 QUICK STATS
{'='*100}
Active applications: {len(active_apps)}
Awaiting response: {len(submitted_apps)}
Due reminders (today): {len([r for r in reminders if r['days_until'] <= 0])}
Overdue reminders: {len([r for r in reminders if r['overdue']])}

{'='*100}
"""
        
        return report
    
    def export_to_calendar(self, output_file: str = 'reminders.ics'):
        """Export reminders to iCalendar format"""
        reminders = self.get_all_reminders()
        
        # Simple ICS format
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Job Application Tracker//Reminders//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""
        
        for item in reminders:
            reminder = item['reminder']
            due_date = datetime.fromisoformat(reminder['due_date'])
            
            # Format dates for ICS
            dtstart = due_date.strftime('%Y%m%dT%H%M%S')
            dtend = (due_date + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')
            dtstamp = datetime.now().strftime('%Y%m%dT%H%M%S')
            
            ics_content += f"""BEGIN:VEVENT
UID:{item['job_id']}-{reminder['id']}@jobtracker
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Job Application: {reminder['message']}
DESCRIPTION:Company: {item['company']}\\nPosition: {item['position']}\\nStatus: {item['status']}
LOCATION:{item['company']}
STATUS:CONFIRMED
PRIORITY:{self._ics_priority(reminder.get('priority', 'medium'))}
END:VEVENT
"""
        
        ics_content += "END:VCALENDAR\n"
        
        # Save to file
        output_path = self.data_dir / output_file
        with open(output_path, 'w') as f:
            f.write(ics_content)
        
        print(f"📅 Calendar exported to: {output_path}")
        print(f"   Import this file into Google Calendar, Outlook, or Apple Calendar")
        
        return str(output_path)
    
    def _ics_priority(self, priority: str) -> int:
        """Convert priority to ICS priority (1-9)"""
        mapping = {
            'critical': 1,
            'high': 3,
            'medium': 5,
            'low': 7
        }
        return mapping.get(priority, 5)

class GitHubActionsFollowUpManager(FollowUpManager):
    """Extended manager with GitHub Actions specific features"""
    
    def auto_create_campaign_reminders(self, campaign_results: Dict) -> int:
        """Automatically create reminders for campaign applications"""
        reminders_created = 0
        
        for campaign in campaign_results.get('campaigns', []):
            for platform_result in campaign.get('platforms', []):
                platform = platform_result['platform'].lower()
                successful = platform_result.get('successful', 0)
                
                if successful > 0:
                    # Get recent submitted applications
                    apps = self.tracker.get_applications_by_platform(platform)
                    recent_submitted = [
                        a for a in apps 
                        if a['status'] == 'submitted'
                    ]
                    
                    # Sort by submission date
                    recent_submitted.sort(
                        key=lambda x: x.get('submitted_at') or x['created_at'],
                        reverse=True
                    )
                    
                    # Create reminders for the most recent submissions
                    for app in recent_submitted[:successful]:
                        if not app.get('reminders'):
                            # Day 3 reminder
                            self.tracker.add_reminder(
                                app['id'],
                                'Check application status - initial review',
                                (datetime.now() + timedelta(days=3)).isoformat(),
                                priority='medium'
                            )
                            
                            # Day 7 reminder
                            self.tracker.add_reminder(
                                app['id'],
                                'Send first follow-up email',
                                (datetime.now() + timedelta(days=7)).isoformat(),
                                priority='high'
                            )
                            
                            # Day 14 reminder
                            self.tracker.add_reminder(
                                app['id'],
                                'Send second follow-up if no response',
                                (datetime.now() + timedelta(days=14)).isoformat(),
                                priority='medium'
                            )
                            
                            reminders_created += 3
        
        return reminders_created
    
    def generate_github_actions_report(self, days_ahead: int = 7) -> Dict:
        """Generate structured report for GitHub Actions"""
        due_reminders = self.get_due_reminders(days_ahead)
        follow_ups = self.tracker.get_follow_up_needed()
        
        report = {
            'summary': {
                'due_reminders': len(due_reminders),
                'follow_ups_needed': len(follow_ups),
                'critical_reminders': len([r for r in due_reminders if r['priority'] == 'critical']),
                'high_priority': len([r for r in due_reminders if r['priority'] == 'high'])
            },
            'due_reminders': [
                {
                    'company': r['company'],
                    'position': r['position'],
                    'message': r['reminder']['message'],
                    'due_date': r['reminder']['due_date'],
                    'priority': r['priority'],
                    'overdue': r['overdue']
                }
                for r in due_reminders
            ],
            'follow_ups': [
                {
                    'company': f['company'],
                    'position': f['position'],
                    'days_since': f['days_since_submission'],
                    'action': f['action'],
                    'priority': f['priority']
                }
                for f in follow_ups
            ]
        }
        
        return report
    
    def export_for_email(self, output_file: str = 'followup_summary.json'):
        """Export summary in email-friendly format"""
        report = self.generate_github_actions_report(days_ahead=14)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file

def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description='Manage follow-ups and reminders for job applications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all due reminders
  python follow_up_reminders.py --show
  
  # Show only critical/high priority
  python follow_up_reminders.py --show --priority critical
  
  # Process reminders interactively
  python follow_up_reminders.py --process
  
  # Generate follow-up email
  python follow_up_reminders.py --email job_12345 --template initial_submission
  
  # Export reminders to calendar
  python follow_up_reminders.py --export-calendar
  
  # Generate report
  python follow_up_reminders.py --report --days 14
        """
    )
    
    parser.add_argument('--show', '-s', action='store_true', help='Show due reminders')
    parser.add_argument('--process', '-p', action='store_true', help='Process reminders interactively')
    parser.add_argument('--priority', choices=['critical', 'high', 'medium', 'low'], help='Filter by priority')
    parser.add_argument('--days', type=int, default=7, help='Days ahead to check (default: 7)')
    parser.add_argument('--email', help='Generate email for job ID')
    parser.add_argument('--template', default='initial_submission', help='Email template name')
    parser.add_argument('--report', '-r', action='store_true', help='Generate follow-up report')
    parser.add_argument('--export-calendar', action='store_true', help='Export to calendar (ICS)')
    parser.add_argument('--data-dir', default='job_search', help='Data directory')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = FollowUpManager(args.data_dir)
    
    # Route commands
    if args.show:
        reminders = manager.get_due_reminders(args.days)
        if args.priority:
            reminders = [r for r in reminders if r['priority'] == args.priority]
        manager.display_reminders(reminders)
    
    elif args.process:
        manager.batch_process_reminders(args.priority)
    
    elif args.email:
        email_content = manager.create_follow_up_email(args.email, args.template)
        print(f"\n{'='*70}")
        print("FOLLOW-UP EMAIL:")
        print(f"{'='*70}")
        print(email_content)
        print(f"{'='*70}")
        
        # Save to file
        output_dir = Path(args.data_dir) / 'follow_ups'
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"email_{args.email}_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write(email_content)
        
        print(f"\n💾 Saved to: {output_file}")
    
    elif args.report:
        report = manager.generate_follow_up_report(args.days)
        print(report)
        
        # Save report
        output_file = Path(args.data_dir) / f"follow_up_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"\n💾 Report saved to: {output_file}")
    
    elif args.export_calendar:
        manager.export_to_calendar()
    
    else:
        # Interactive menu
        print("""
╔════════════════════════════════════════════════════════════════════╗
║              FOLLOW-UP REMINDER MANAGER                            ║
╚════════════════════════════════════════════════════════════════════╝

Choose an option:
  1. Show due reminders
  2. Process reminders (batch)
  3. Generate follow-up email
  4. Generate follow-up report
  5. Export to calendar
  0. Exit
""")
        
        while True:
            choice = input("\nSelect option: ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            
            elif choice == '1':
                days = input("Days ahead to check (default 7): ").strip()
                days = int(days) if days else 7
                reminders = manager.get_due_reminders(days)
                manager.display_reminders(reminders)
            
            elif choice == '2':
                priority = input("Filter by priority (critical/high/medium/low or Enter for all): ").strip()
                priority = priority if priority else None
                manager.batch_process_reminders(priority)
            
            elif choice == '3':
                job_id = input("Job ID: ").strip()
                print("\nTemplates: initial_submission, post_interview, second_follow_up")
                template = input("Template name: ").strip() or 'initial_submission'
                
                try:
                    email = manager.create_follow_up_email(job_id, template)
                    print(f"\n{'='*70}")
                    print(email)
                    print(f"{'='*70}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            elif choice == '4':
                days = input("Days ahead (default 14): ").strip()
                days = int(days) if days else 14
                report = manager.generate_follow_up_report(days)
                print(report)
            
            elif choice == '5':
                manager.export_to_calendar()
            
            else:
                print("Invalid option")


if __name__ == '__main__':
    main()
