#!/usr/bin/env python3
"""
LinkedIn Automation - Smart Connection & Engagement System
Automates LinkedIn networking within platform limits and best practices
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import time
import random

class LinkedInAutomation:
    def __init__(self, data_dir: str = "job_search"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # LinkedIn rate limits (conservative to avoid restrictions)
        self.DAILY_CONNECTION_LIMIT = 5  # Safe limit (LinkedIn allows ~100)
        self.DAILY_MESSAGE_LIMIT = 10
        self.DAILY_PROFILE_VIEW_LIMIT = 50
        self.WEEKLY_CONNECTION_LIMIT = 35
        
        # Data files
        self.activity_file = self.data_dir / "linkedin_activity.json"
        self.queue_file = self.data_dir / "linkedin_queue.json"
        self.connections_file = self.data_dir / "linkedin_connections.json"
        
        self.activity = self._load_json(self.activity_file, self._default_activity())
        self.queue = self._load_json(self.queue_file, self._default_queue())
        self.connections = self._load_json(self.connections_file, [])
        
        self._reset_daily_limits()
    
    def _load_json(self, filepath: Path, default):
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, filepath: Path, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _default_activity(self):
        return {
            "last_reset": datetime.now().date().isoformat(),
            "daily_connections": 0,
            "daily_messages": 0,
            "daily_profile_views": 0,
            "weekly_connections": 0,
            "week_start": datetime.now().date().isoformat(),
            "total_connections": 0,
            "response_rate": 0.0
        }
    
    def _default_queue(self):
        return {
            "pending_connections": [],
            "pending_messages": [],
            "pending_profile_views": [],
            "scheduled_follow_ups": []
        }
    
    def _reset_daily_limits(self):
        """Reset daily counters if it's a new day"""
        today = datetime.now().date().isoformat()
        
        if self.activity["last_reset"] != today:
            self.activity["last_reset"] = today
            self.activity["daily_connections"] = 0
            self.activity["daily_messages"] = 0
            self.activity["daily_profile_views"] = 0
            self._save_json(self.activity_file, self.activity)
        
        # Reset weekly counter
        week_start = datetime.fromisoformat(self.activity["week_start"])
        if (datetime.now().date() - week_start.date()).days >= 7:
            self.activity["weekly_connections"] = 0
            self.activity["week_start"] = datetime.now().date().isoformat()
            self._save_json(self.activity_file, self.activity)
    
    def add_connection_target(self, profile_url: str, name: str, 
                             company: str, position: str, 
                             connection_reason: str, priority: str = "medium"):
        """Add someone to connection queue with personalized message"""
        
        # Generate personalized connection message
        message = self._generate_connection_message(name, company, position, connection_reason)
        
        target = {
            "id": f"CONN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "profile_url": profile_url,
            "name": name,
            "company": company,
            "position": position,
            "reason": connection_reason,
            "message": message,
            "priority": priority,
            "added_date": datetime.now().isoformat(),
            "status": "queued"
        }
        
        self.queue["pending_connections"].append(target)
        self._save_json(self.queue_file, self.queue)
        
        return {
            "success": True,
            "target_id": target["id"],
            "message": f"Added {name} to connection queue",
            "estimated_send": self._estimate_send_time()
        }
    
    def _generate_connection_message(self, name: str, company: str, 
                                    position: str, reason: str) -> str:
        """Generate personalized connection request message"""
        
        templates = {
            "job_application": f"""Hi {name.split()[0]},

I recently applied for a position at {company} and was impressed by the team's work. I'd love to connect and learn more about {company}'s culture and the exciting projects you're working on.

Looking forward to connecting!""",
            
            "industry_peer": f"""Hi {name.split()[0]},

I came across your profile and noticed we're both in {position.split()[0] if position else 'the industry'}. I'd love to connect and exchange insights about our field.

Best regards!""",
            
            "mutual_interest": f"""Hi {name.split()[0]},

I noticed your work at {company} aligns with my professional interests. I'd appreciate the opportunity to connect and learn from your experience.

Thanks!""",
            
            "referral_request": f"""Hi {name.split()[0]},

I'm very interested in opportunities at {company}. Given your experience there, I'd greatly appreciate connecting to learn more about the company and potential openings.

Thank you for considering!"""
        }
        
        return templates.get(reason, templates["mutual_interest"])
    
    def process_daily_connections(self, manual_mode: bool = False) -> Dict:
        """Process today's connection requests"""
        
        results = {
            "connections_sent": 0,
            "remaining_daily": 0,
            "queued": len(self.queue["pending_connections"]),
            "actions": []
        }
        
        # Check if we've hit daily limit
        if self.activity["daily_connections"] >= self.DAILY_CONNECTION_LIMIT:
            results["remaining_daily"] = 0
            results["message"] = "Daily connection limit reached"
            return results
        
        # Check weekly limit
        if self.activity["weekly_connections"] >= self.WEEKLY_CONNECTION_LIMIT:
            results["message"] = "Weekly connection limit reached"
            return results
        
        # Sort queue by priority
        self.queue["pending_connections"].sort(
            key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 1)
        )
        
        # Process connections
        available_slots = min(
            self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"],
            self.WEEKLY_CONNECTION_LIMIT - self.activity["weekly_connections"]
        )
        
        for i in range(min(available_slots, len(self.queue["pending_connections"]))):
            target = self.queue["pending_connections"][i]
            
            if manual_mode:
                # In manual mode, just provide instructions
                action = {
                    "type": "manual_instruction",
                    "target": target["name"],
                    "company": target["company"],
                    "profile_url": target["profile_url"],
                    "message": target["message"],
                    "instruction": f"Visit {target['profile_url']}, click 'Connect', and send this personalized message"
                }
            else:
                # In automated mode, log the action (actual automation requires browser automation)
                action = {
                    "type": "automated_log",
                    "target": target["name"],
                    "company": target["company"],
                    "message": "Connection request logged (requires browser automation to execute)"
                }
            
            results["actions"].append(action)
            
            # Move to connections tracking
            connection_record = {
                **target,
                "connection_date": datetime.now().isoformat(),
                "status": "pending",
                "follow_up_date": (datetime.now() + timedelta(days=7)).isoformat()
            }
            self.connections.append(connection_record)
            
            # Update counters
            self.activity["daily_connections"] += 1
            self.activity["weekly_connections"] += 1
            self.activity["total_connections"] += 1
            results["connections_sent"] += 1
        
        # Remove processed items from queue
        self.queue["pending_connections"] = self.queue["pending_connections"][available_slots:]
        
        results["remaining_daily"] = self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"]
        results["message"] = f"Processed {results['connections_sent']} connections"
        
        # Save data
        self._save_json(self.activity_file, self.activity)
        self._save_json(self.queue_file, self.queue)
        self._save_json(self.connections_file, self.connections)
        
        return results
    
    def add_follow_up_message(self, connection_id: str, message_type: str = "general"):
        """Schedule follow-up message for accepted connection"""
        
        templates = {
            "general": """Thanks for connecting! I'm exploring opportunities in [industry/role] and would love to hear about your experience at [Company]. 

Would you be open to a brief 15-minute coffee chat sometime?""",
            
            "referral": """Thanks for connecting! I'm very interested in opportunities at [Company] and noticed you've been there for a while.

Would you be open to discussing your experience and potentially providing insights on the team/culture?""",
            
            "informational": """Thanks for connecting! I'm researching [specific area] and your background in [their expertise] is really impressive.

Would you have 15 minutes for an informational chat about your career path?"""
        }
        
        message = {
            "id": f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "connection_id": connection_id,
            "message_type": message_type,
            "message": templates.get(message_type, templates["general"]),
            "scheduled_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "status": "scheduled"
        }
        
        self.queue["pending_messages"].append(message)
        self._save_json(self.queue_file, self.queue)
        
        return {"success": True, "message_id": message["id"]}
    
    def get_daily_status(self) -> Dict:
        """Get current day's LinkedIn activity status"""
        
        return {
            "date": datetime.now().date().isoformat(),
            "connections": {
                "sent_today": self.activity["daily_connections"],
                "limit": self.DAILY_CONNECTION_LIMIT,
                "remaining": self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"]
            },
            "weekly_connections": {
                "sent_this_week": self.activity["weekly_connections"],
                "limit": self.WEEKLY_CONNECTION_LIMIT,
                "remaining": self.WEEKLY_CONNECTION_LIMIT - self.activity["weekly_connections"]
            },
            "queued": {
                "connections": len(self.queue["pending_connections"]),
                "messages": len(self.queue["pending_messages"]),
                "follow_ups": len(self.queue["scheduled_follow_ups"])
            },
            "total_network": self.activity["total_connections"],
            "response_rate": f"{self.activity['response_rate']:.1f}%"
        }
    
    def get_pending_actions(self) -> Dict:
        """Get all pending LinkedIn actions for today"""
        
        actions = {
            "connections_to_send": [],
            "messages_to_send": [],
            "follow_ups_due": [],
            "profiles_to_view": []
        }
        
        # Get today's connections
        available = self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"]
        actions["connections_to_send"] = self.queue["pending_connections"][:available]
        
        # Get scheduled messages for today
        today = datetime.now().date().isoformat()
        actions["messages_to_send"] = [
            msg for msg in self.queue["pending_messages"]
            if msg["scheduled_date"][:10] <= today and msg["status"] == "scheduled"
        ]
        
        # Get due follow-ups
        actions["follow_ups_due"] = [
            conn for conn in self.connections
            if conn.get("follow_up_date", "")[:10] <= today and conn["status"] == "connected"
        ]
        
        return actions
    
    def _estimate_send_time(self) -> str:
        """Estimate when queued connection will be sent"""
        
        queue_position = len(self.queue["pending_connections"])
        remaining_today = self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"]
        
        if queue_position <= remaining_today:
            return "Today"
        else:
            days_ahead = (queue_position - remaining_today) // self.DAILY_CONNECTION_LIMIT + 1
            return f"In {days_ahead} day{'s' if days_ahead > 1 else ''}"
    
    def generate_daily_report(self) -> str:
        """Generate daily LinkedIn activity report"""
        
        status = self.get_daily_status()
        actions = self.get_pending_actions()
        
        report = f"""
# LinkedIn Daily Report - {datetime.now().strftime('%Y-%m-%d')}

## Today's Activity
- Connections Sent: {status['connections']['sent_today']}/{status['connections']['limit']}
- Remaining Today: {status['connections']['remaining']}
- Weekly Progress: {status['weekly_connections']['sent_this_week']}/{status['weekly_connections']['limit']}

## Pending Actions
- Connections to Send: {len(actions['connections_to_send'])}
- Messages to Send: {len(actions['messages_to_send'])}
- Follow-ups Due: {len(actions['follow_ups_due'])}

## Network Statistics
- Total Connections: {status['total_network']}
- Response Rate: {status['response_rate']}

## Next Actions
"""
        
        if actions['connections_to_send']:
            report += "\n### Connections to Send Today:\n"
            for conn in actions['connections_to_send']:
                report += f"- {conn['name']} ({conn['company']}) - {conn['reason']}\n"
        
        if actions['messages_to_send']:
            report += "\n### Messages to Send:\n"
            for msg in actions['messages_to_send']:
                report += f"- Follow-up message scheduled\n"
        
        if actions['follow_ups_due']:
            report += "\n### Follow-ups Due:\n"
            for follow_up in actions['follow_ups_due']:
                report += f"- {follow_up['name']} ({follow_up['company']})\n"
        
        return report

if __name__ == "__main__":
    # Example usage
    linkedin = LinkedInAutomation()
    
    # Add connection targets
    linkedin.add_connection_target(
        profile_url="https://linkedin.com/in/example",
        name="Jane Smith",
        company="Tech Corp",
        position="Senior Engineer",
        connection_reason="job_application",
        priority="high"
    )
    
    # Get daily status
    status = linkedin.get_daily_status()
    print(json.dumps(status, indent=2))
    
    # Generate report
    report = linkedin.generate_daily_report()
    print(report)
