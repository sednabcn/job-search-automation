#!/usr/bin/env python3
"""
Advanced LinkedIn Networking Automation
Specialized for Data Science, AI/ML Engineers, Finance, and Trading roles
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import random

class AdvancedLinkedInNetworking:
    def __init__(self, data_dir: str = "job_search"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Rate limits
        self.DAILY_CONNECTION_LIMIT = 5
        self.DAILY_MESSAGE_LIMIT = 10
        self.WEEKLY_CONNECTION_LIMIT = 35
        
        # Data files
        self.activity_file = self.data_dir / "linkedin_advanced_activity.json"
        self.targets_file = self.data_dir / "linkedin_targets.json"
        self.campaigns_file = self.data_dir / "linkedin_campaigns.json"
        self.conversations_file = self.data_dir / "linkedin_conversations.json"
        
        self.activity = self._load_json(self.activity_file, self._default_activity())
        self.targets = self._load_json(self.targets_file, [])
        self.campaigns = self._load_json(self.campaigns_file, [])
        self.conversations = self._load_json(self.conversations_file, [])
        
        # Industry-specific targeting
        self.TARGET_INDUSTRIES = {
            "data_science_ai": {
                "titles": [
                    "Data Scientist", "Machine Learning Engineer", "AI Engineer",
                    "ML Research Scientist", "Applied Scientist", "Research Engineer",
                    "Deep Learning Engineer", "NLP Engineer", "Computer Vision Engineer",
                    "AI Product Manager", "Head of AI", "Director of Machine Learning",
                    "Staff Machine Learning Engineer", "Principal Data Scientist"
                ],
                "companies": [
                    "OpenAI", "Anthropic", "Google DeepMind", "Meta AI", "Microsoft Research",
                    "Amazon AWS AI", "Scale AI", "Hugging Face", "Cohere", "Stability AI",
                    "DataRobot", "Databricks", "Snowflake", "Palantir", "C3.AI"
                ],
                "keywords": [
                    "LLM", "GPT", "Transformer", "PyTorch", "TensorFlow", "MLOps",
                    "Computer Vision", "NLP", "Reinforcement Learning", "GenAI"
                ]
            },
            "finance": {
                "titles": [
                    "Quantitative Analyst", "Quantitative Researcher", "Quant Developer",
                    "Risk Analyst", "Portfolio Manager", "Financial Engineer",
                    "Investment Analyst", "Equity Research Analyst", "Credit Analyst",
                    "VP of Quantitative Research", "Head of Risk", "Chief Risk Officer"
                ],
                "companies": [
                    "Jane Street", "Citadel", "Two Sigma", "Renaissance Technologies",
                    "DE Shaw", "Jump Trading", "Goldman Sachs", "Morgan Stanley",
                    "JPMorgan", "Blackrock", "Bridgewater", "AQR Capital"
                ],
                "keywords": [
                    "Quantitative Finance", "Risk Management", "Portfolio Optimization",
                    "Derivatives", "Fixed Income", "Credit Risk", "Market Risk"
                ]
            },
            "trading": {
                "titles": [
                    "Quantitative Trader", "Algorithmic Trader", "High Frequency Trader",
                    "Options Trader", "Market Maker", "Prop Trader", "Systematic Trader",
                    "Head of Trading", "Trading Strategist", "Execution Trader"
                ],
                "companies": [
                    "Citadel Securities", "Jane Street", "Virtu Financial", "Jump Trading",
                    "Tower Research", "Hudson River Trading", "IMC Trading", "Optiver",
                    "SIG (Susquehanna)", "DRW Trading", "Flow Traders", "Akuna Capital"
                ],
                "keywords": [
                    "HFT", "Market Making", "Algo Trading", "Order Execution",
                    "Quantitative Trading", "Statistical Arbitrage", "Options Trading"
                ]
            }
        }
    
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
            "weekly_connections": 0,
            "week_start": datetime.now().date().isoformat(),
            "total_connections": 0,
            "response_rate": 0.0,
            "industry_breakdown": {
                "data_science_ai": 0,
                "finance": 0,
                "trading": 0
            }
        }
    
    def create_targeted_campaign(self, campaign_name: str, industry: str, 
                                 target_level: str = "mid_senior",
                                 target_companies: List[str] = None,
                                 daily_target: int = 3) -> Dict:
        """Create a targeted networking campaign"""
        
        if industry not in self.TARGET_INDUSTRIES:
            return {"success": False, "error": f"Invalid industry. Choose: {list(self.TARGET_INDUSTRIES.keys())}"}
        
        campaign_id = f"CAMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        campaign = {
            "id": campaign_id,
            "name": campaign_name,
            "industry": industry,
            "target_level": target_level,
            "target_companies": target_companies or self.TARGET_INDUSTRIES[industry]["companies"],
            "target_titles": self.TARGET_INDUSTRIES[industry]["titles"],
            "daily_target": daily_target,
            "created_date": datetime.now().isoformat(),
            "status": "active",
            "stats": {
                "connections_sent": 0,
                "connections_accepted": 0,
                "messages_sent": 0,
                "responses_received": 0,
                "meetings_scheduled": 0
            }
        }
        
        self.campaigns.append(campaign)
        self._save_json(self.campaigns_file, self.campaigns)
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": f"Campaign '{campaign_name}' created for {industry}",
            "target_companies": campaign["target_companies"][:5]
        }
    
    def add_connection_target(self, profile_url: str, name: str, 
                             company: str, position: str, industry: str,
                             campaign_id: str = None, priority: str = "medium",
                             mutual_connections: int = 0) -> Dict:
        """Add targeted connection with industry-specific messaging"""
        
        target_id = f"TARGET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generate industry-specific message
        message = self._generate_industry_message(
            name, company, position, industry, mutual_connections
        )
        
        target = {
            "id": target_id,
            "profile_url": profile_url,
            "name": name,
            "company": company,
            "position": position,
            "industry": industry,
            "campaign_id": campaign_id,
            "priority": priority,
            "mutual_connections": mutual_connections,
            "message": message,
            "added_date": datetime.now().isoformat(),
            "status": "queued",
            "connection_sent_date": None,
            "connection_accepted_date": None,
            "follow_up_scheduled": None
        }
        
        self.targets.append(target)
        self._save_json(self.targets_file, self.targets)
        
        return {
            "success": True,
            "target_id": target_id,
            "message_preview": message[:100] + "...",
            "estimated_send": self._estimate_send_time()
        }
    
    def _generate_industry_message(self, name: str, company: str, 
                                   position: str, industry: str,
                                   mutual_connections: int = 0) -> str:
        """Generate personalized connection message based on industry"""
        
        first_name = name.split()[0]
        
        # Industry-specific templates
        templates = {
            "data_science_ai": [
                f"Hi {first_name},\n\nI came across your work at {company} and was impressed by your experience in {position}. I'm exploring opportunities in ML/AI and would love to connect and learn from your journey in the field.\n\nLooking forward to connecting!",
                
                f"Hi {first_name},\n\nYour background in AI at {company} caught my attention. I'm particularly interested in {self._get_ai_interest()}. Would love to connect and exchange insights about the field.\n\nBest regards!",
                
                f"Hi {first_name},\n\nI noticed your role as {position} at {company}. As someone passionate about ML/AI, I'd appreciate the opportunity to connect and learn about {company}'s approach to AI innovation.\n\nThanks for considering!"
            ],
            "finance": [
                f"Hi {first_name},\n\nYour experience in quantitative finance at {company} is impressive. I'm pursuing opportunities in quant research/development and would greatly appreciate connecting to learn from your expertise.\n\nLooking forward to it!",
                
                f"Hi {first_name},\n\nI came across your profile and was struck by your work at {company}. I'm interested in {self._get_finance_interest()} and would value connecting with someone with your background.\n\nBest regards!",
                
                f"Hi {first_name},\n\nAs someone exploring quantitative finance, I'm impressed by your role at {company}. Would love to connect and learn about your path in the industry.\n\nThank you!"
            ],
            "trading": [
                f"Hi {first_name},\n\nYour experience in systematic trading at {company} is fascinating. I'm exploring opportunities in algo trading and would appreciate connecting to learn from your journey.\n\nLooking forward to connecting!",
                
                f"Hi {first_name},\n\nI noticed your background in {position} at {company}. As someone interested in quantitative trading strategies, I'd value the opportunity to connect and learn from your experience.\n\nBest regards!",
                
                f"Hi {first_name},\n\nYour work at {company} caught my attention. I'm passionate about algorithmic trading and would appreciate connecting to exchange insights about the field.\n\nThank you for considering!"
            ]
        }
        
        # Add mutual connection reference if applicable
        mutual_ref = ""
        if mutual_connections > 0:
            mutual_ref = f" We have {mutual_connections} mutual connection{'s' if mutual_connections > 1 else ''}, which encouraged me to reach out."
        
        # Select random template and add mutual connection reference
        template = random.choice(templates.get(industry, templates["data_science_ai"]))
        
        if mutual_ref:
            # Insert mutual reference after first sentence
            parts = template.split('\n\n', 1)
            if len(parts) == 2:
                template = parts[0] + mutual_ref + "\n\n" + parts[1]
        
        return template
    
    def _get_ai_interest(self) -> str:
        """Get random AI interest area"""
        interests = [
            "LLM fine-tuning and deployment",
            "reinforcement learning applications",
            "computer vision systems",
            "NLP and transformer architectures",
            "MLOps and model deployment",
            "generative AI applications"
        ]
        return random.choice(interests)
    
    def _get_finance_interest(self) -> str:
        """Get random finance interest area"""
        interests = [
            "quantitative risk management",
            "portfolio optimization strategies",
            "derivative pricing models",
            "statistical arbitrage",
            "credit risk modeling",
            "systematic trading strategies"
        ]
        return random.choice(interests)
    
    def process_daily_connections(self, campaign_id: str = None) -> Dict:
        """Process daily connections for specific campaign or all"""
        
        results = {
            "connections_processed": 0,
            "remaining_daily": 0,
            "actions": [],
            "by_industry": {}
        }
        
        # Check limits
        if self.activity["daily_connections"] >= self.DAILY_CONNECTION_LIMIT:
            results["message"] = "Daily connection limit reached"
            return results
        
        # Filter targets
        available_targets = [
            t for t in self.targets 
            if t["status"] == "queued" and 
            (campaign_id is None or t.get("campaign_id") == campaign_id)
        ]
        
        # Sort by priority and mutual connections
        available_targets.sort(
            key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 1),
                -x.get("mutual_connections", 0)
            )
        )
        
        # Process connections
        available_slots = self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"]
        
        for target in available_targets[:available_slots]:
            action = {
                "type": "connection_request",
                "target_id": target["id"],
                "name": target["name"],
                "company": target["company"],
                "position": target["position"],
                "industry": target["industry"],
                "profile_url": target["profile_url"],
                "message": target["message"],
                "priority": target["priority"],
                "mutual_connections": target.get("mutual_connections", 0),
                "instruction": f"1. Visit: {target['profile_url']}\n2. Click 'Connect'\n3. Add note and paste the message above"
            }
            
            results["actions"].append(action)
            
            # Update target status
            target["status"] = "pending"
            target["connection_sent_date"] = datetime.now().isoformat()
            target["follow_up_scheduled"] = (datetime.now() + timedelta(days=7)).isoformat()
            
            # Update stats
            industry = target["industry"]
            results["by_industry"][industry] = results["by_industry"].get(industry, 0) + 1
            self.activity["daily_connections"] += 1
            self.activity["weekly_connections"] += 1
            self.activity["industry_breakdown"][industry] = self.activity["industry_breakdown"].get(industry, 0) + 1
            results["connections_processed"] += 1
        
        results["remaining_daily"] = self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"]
        results["message"] = f"Processed {results['connections_processed']} connections"
        
        # Save data
        self._save_json(self.targets_file, self.targets)
        self._save_json(self.activity_file, self.activity)
        
        return results
    
    def create_follow_up_sequence(self, target_id: str) -> Dict:
        """Create multi-touch follow-up sequence after connection"""
        
        target = self._get_target(target_id)
        if not target:
            return {"success": False, "error": "Target not found"}
        
        if target["status"] != "connected":
            return {"success": False, "error": "Connection not yet accepted"}
        
        # Industry-specific follow-up sequences
        sequences = {
            "data_science_ai": [
                {
                    "day": 3,
                    "type": "thank_you",
                    "message": f"Hi {target['name'].split()[0]},\n\nThanks for connecting! I'm curious about {target['company']}'s approach to ML infrastructure and deployment. Would you be open to a brief 15-minute chat about your experience?\n\nBest regards"
                },
                {
                    "day": 14,
                    "type": "value_share",
                    "message": f"Hi {target['name'].split()[0]},\n\nI recently came across this interesting paper on [relevant AI topic] and thought you might find it valuable given your work at {target['company']}.\n\n[Link would go here]\n\nWould love to hear your thoughts!"
                },
                {
                    "day": 30,
                    "type": "informational",
                    "message": f"Hi {target['name'].split()[0]},\n\nI hope you're doing well! I'm exploring ML engineering roles and would greatly appreciate 15 minutes of your time to learn about your career path and {target['company']}'s team culture.\n\nWould next week work for a quick call?"
                }
            ],
            "finance": [
                {
                    "day": 3,
                    "type": "thank_you",
                    "message": f"Hi {target['name'].split()[0]},\n\nThanks for connecting! Your work in quantitative finance at {target['company']} is impressive. Would you be open to a brief chat about your experience in the field?\n\nBest regards"
                },
                {
                    "day": 14,
                    "type": "value_share",
                    "message": f"Hi {target['name'].split()[0]},\n\nI came across an interesting piece on [quantitative finance topic] that reminded me of your work. Thought you might find it relevant.\n\n[Link]\n\nWould love your perspective!"
                },
                {
                    "day": 30,
                    "type": "informational",
                    "message": f"Hi {target['name'].split()[0]},\n\nI hope all is well! I'm actively exploring quant roles and would greatly value 15 minutes to learn about your journey and {target['company']}'s culture.\n\nWould you be available for a brief call?"
                }
            ],
            "trading": [
                {
                    "day": 3,
                    "type": "thank_you",
                    "message": f"Hi {target['name'].split()[0]},\n\nThanks for connecting! Your experience in systematic trading at {target['company']} is fascinating. Would you be open to a brief chat about the field?\n\nBest"
                },
                {
                    "day": 14,
                    "type": "value_share",
                    "message": f"Hi {target['name'].split()[0]},\n\nSaw this analysis on market microstructure and thought of your work at {target['company']}. Might be of interest.\n\n[Link]\n\nCurious about your take!"
                },
                {
                    "day": 30,
                    "type": "informational",
                    "message": f"Hi {target['name'].split()[0]},\n\nHope you're well! I'm exploring algo trading opportunities and would love 15 minutes to learn about your path and insights on {target['company']}.\n\nFree for a quick call?"
                }
            ]
        }
        
        industry = target.get("industry", "data_science_ai")
        sequence = sequences.get(industry, sequences["data_science_ai"])
        
        # Create conversation tracking
        conversation_id = f"CONV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conversation = {
            "id": conversation_id,
            "target_id": target_id,
            "name": target["name"],
            "company": target["company"],
            "industry": industry,
            "sequence": sequence,
            "current_step": 0,
            "started_date": datetime.now().isoformat(),
            "status": "active",
            "response_received": False
        }
        
        self.conversations.append(conversation)
        self._save_json(self.conversations_file, self.conversations)
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "sequence_steps": len(sequence),
            "first_message_date": (datetime.now() + timedelta(days=sequence[0]["day"])).isoformat()
        }
    
    def get_daily_tasks(self) -> Dict:
        """Get comprehensive daily LinkedIn tasks"""
        
        # Reset daily limits if needed
        self._reset_daily_limits()
        
        tasks = {
            "connections_to_send": [],
            "messages_to_send": [],
            "follow_ups_due": [],
            "content_engagement": [],
            "profile_views": []
        }
        
        # 1. Connection requests
        connection_result = self.process_daily_connections()
        tasks["connections_to_send"] = connection_result["actions"]
        
        # 2. Scheduled messages
        today = datetime.now().date().isoformat()
        for conv in self.conversations:
            if conv["status"] != "active":
                continue
            
            current_step = conv["current_step"]
            if current_step < len(conv["sequence"]):
                step = conv["sequence"][current_step]
                send_date = datetime.fromisoformat(conv["started_date"]) + timedelta(days=step["day"])
                
                if send_date.date().isoformat() <= today:
                    tasks["messages_to_send"].append({
                        "conversation_id": conv["id"],
                        "name": conv["name"],
                        "company": conv["company"],
                        "message_type": step["type"],
                        "message": step["message"],
                        "days_since_connection": step["day"]
                    })
        
        # 3. Follow-ups for non-responders
        for target in self.targets:
            if target["status"] == "connected" and not target.get("response_received"):
                last_message = target.get("last_message_date")
                if last_message:
                    days_since = (datetime.now() - datetime.fromisoformat(last_message)).days
                    if days_since >= 7:
                        tasks["follow_ups_due"].append({
                            "target_id": target["id"],
                            "name": target["name"],
                            "company": target["company"],
                            "days_since_last_message": days_since,
                            "suggested_action": "Gentle follow-up or value-add message"
                        })
        
        # 4. Content engagement recommendations
        tasks["content_engagement"] = self._get_engagement_recommendations()
        
        # 5. Strategic profile views
        tasks["profile_views"] = self._get_strategic_profile_views()
        
        return tasks
    
    def _get_engagement_recommendations(self) -> List[Dict]:
        """Get daily content engagement recommendations"""
        
        recommendations = []
        
        # Recommend engaging with connections' content
        connected_targets = [t for t in self.targets if t["status"] == "connected"][:5]
        
        for target in connected_targets:
            recommendations.append({
                "type": "engage_with_post",
                "name": target["name"],
                "company": target["company"],
                "action": "Like/comment on their recent post",
                "why": "Stay top of mind and build rapport"
            })
        
        # Recommend sharing relevant content
        recommendations.append({
            "type": "share_content",
            "topic": "AI/ML insights" if self.activity["industry_breakdown"]["data_science_ai"] > 0 else "Quant finance insights",
            "action": "Share article or insight",
            "why": "Demonstrate expertise and provide value"
        })
        
        return recommendations[:3]
    
    def _get_strategic_profile_views(self) -> List[Dict]:
        """Get strategic profile views for the day"""
        
        views = []
        
        # View profiles of pending connections (increases acceptance)
        pending = [t for t in self.targets if t["status"] == "pending"][:10]
        
        for target in pending:
            days_pending = (datetime.now() - datetime.fromisoformat(target["connection_sent_date"])).days
            if days_pending < 7:
                views.append({
                    "name": target["name"],
                    "profile_url": target["profile_url"],
                    "reason": f"Pending connection ({days_pending} days)",
                    "action": "View profile to stay visible"
                })
        
        return views[:5]
    
    def _get_target(self, target_id: str) -> Optional[Dict]:
        """Get target by ID"""
        for target in self.targets:
            if target["id"] == target_id:
                return target
        return None

    def mark_connection_accepted(self, target_id: str) -> Dict:
        """Mark a connection request as accepted"""
        target = self._get_target(target_id)
        if not target:
            return {"success": False, "error": "Target not found"}
        
        if target["status"] != "pending":
            return {"success": False, "error": f"Target status is '{target['status']}', not 'pending'"}
        
        target["status"] = "connected"
        target["connection_accepted_date"] = datetime.now().isoformat()
        
        # Update campaign stats
        if target.get("campaign_id"):
            campaign = self._get_campaign(target["campaign_id"])
            if campaign:
                campaign["stats"]["connections_accepted"] += 1
                self._save_json(self.campaigns_file, self.campaigns)
        
        self._save_json(self.targets_file, self.targets)
        
        return {
            "success": True,
            "message": f"Connection accepted: {target['name']} at {target['company']}",
            "target_id": target_id,
            "next_step": "Create follow-up sequence with create_follow_up_sequence()"
        }
    
    def mark_connection_rejected(self, target_id: str) -> Dict:
        """Mark a connection request as rejected/expired"""
        target = self._get_target(target_id)
        if not target:
            return {"success": False, "error": "Target not found"}
        
        target["status"] = "rejected"
        target["rejection_date"] = datetime.now().isoformat()
        
        self._save_json(self.targets_file, self.targets)
        
        return {
            "success": True,
            "message": f"Connection marked as rejected: {target['name']}"
        }
    
    def record_message_sent(self, conversation_id: str, message_type: str = None) -> Dict:
        """Record that a message was sent in a conversation"""
        conversation = self._get_conversation(conversation_id)
        if not conversation:
            return {"success": False, "error": "Conversation not found"}
        
        # Update conversation
        if conversation["current_step"] < len(conversation["sequence"]):
            conversation["current_step"] += 1
        
        # Update target
        target = self._get_target(conversation["target_id"])
        if target:
            target["last_message_date"] = datetime.now().isoformat()
            target["last_message_type"] = message_type or "follow_up"
        
        # Update campaign stats
        if target and target.get("campaign_id"):
            campaign = self._get_campaign(target["campaign_id"])
            if campaign:
                campaign["stats"]["messages_sent"] += 1
                self._save_json(self.campaigns_file, self.campaigns)
        
        # Update daily counter
        self.activity["daily_messages"] += 1
        
        self._save_json(self.conversations_file, self.conversations)
        self._save_json(self.targets_file, self.targets)
        self._save_json(self.activity_file, self.activity)
        
        return {
            "success": True,
            "message": "Message sent recorded",
            "conversation_step": f"{conversation['current_step']}/{len(conversation['sequence'])}"
        }
    
    def record_response_received(self, target_id: str, response_text: str = None) -> Dict:
        """Record that a target responded to a message"""
        target = self._get_target(target_id)
        if not target:
            return {"success": False, "error": "Target not found"}
        
        target["response_received"] = True
        target["last_response_date"] = datetime.now().isoformat()
        if response_text:
            target["last_response_text"] = response_text[:500]  # Store preview
        
        # Update conversation
        for conv in self.conversations:
            if conv["target_id"] == target_id:
                conv["response_received"] = True
                conv["status"] = "engaged"
                break
        
        # Update campaign stats
        if target.get("campaign_id"):
            campaign = self._get_campaign(target["campaign_id"])
            if campaign:
                campaign["stats"]["responses_received"] += 1
                self._save_json(self.campaigns_file, self.campaigns)
        
        # Update overall response rate
        self._update_response_rate()
        
        self._save_json(self.targets_file, self.targets)
        self._save_json(self.conversations_file, self.conversations)
        
        return {
            "success": True,
            "message": f"Response recorded from {target['name']}",
            "next_step": "Continue conversation or schedule meeting"
        }
    
    def record_meeting_scheduled(self, target_id: str, meeting_date: str, 
                                 meeting_type: str = "informational") -> Dict:
        """Record that a meeting was scheduled"""
        target = self._get_target(target_id)
        if not target:
            return {"success": False, "error": "Target not found"}
        
        target["meeting_scheduled"] = True
        target["meeting_date"] = meeting_date
        target["meeting_type"] = meeting_type
        target["status"] = "meeting_scheduled"
        
        # Update conversation
        for conv in self.conversations:
            if conv["target_id"] == target_id:
                conv["status"] = "meeting_scheduled"
                break
        
        # Update campaign stats
        if target.get("campaign_id"):
            campaign = self._get_campaign(target["campaign_id"])
            if campaign:
                campaign["stats"]["meetings_scheduled"] += 1
                self._save_json(self.campaigns_file, self.campaigns)
        
        self._save_json(self.targets_file, self.targets)
        self._save_json(self.conversations_file, self.conversations)
        
        return {
            "success": True,
            "message": f"Meeting scheduled with {target['name']} on {meeting_date}",
            "meeting_type": meeting_type
        }
    
    def _get_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Get campaign by ID"""
        for campaign in self.campaigns:
            if campaign["id"] == campaign_id:
                return campaign
        return None
    
    def _get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID"""
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                return conv
        return None
    
    def _update_response_rate(self):
        """Calculate and update overall response rate"""
        total_messages = sum(1 for t in self.targets if t.get("last_message_date"))
        total_responses = sum(1 for t in self.targets if t.get("response_received"))
        
        if total_messages > 0:
            self.activity["response_rate"] = (total_responses / total_messages) * 100
        
        self._save_json(self.activity_file, self.activity)
    
    def _reset_daily_limits(self):
        """Reset daily counters"""
        today = datetime.now().date().isoformat()
        if self.activity["last_reset"] != today:
            self.activity["last_reset"] = today
            self.activity["daily_connections"] = 0
            self.activity["daily_messages"] = 0
            self._save_json(self.activity_file, self.activity)
        
        # Reset weekly counter if needed
        week_start = datetime.fromisoformat(self.activity["week_start"]).date()
        days_since_start = (datetime.now().date() - week_start).days
        if days_since_start >= 7:
            self.activity["weekly_connections"] = 0
            self.activity["week_start"] = datetime.now().date().isoformat()
            self._save_json(self.activity_file, self.activity)
            
    def _estimate_send_time(self) -> str:
        """Estimate when queued connection will be sent"""
        queued = len([t for t in self.targets if t["status"] == "queued"])
        remaining_today = self.DAILY_CONNECTION_LIMIT - self.activity["daily_connections"]
        
        if queued <= remaining_today:
            return "Today"
        else:
            days = (queued - remaining_today) // self.DAILY_CONNECTION_LIMIT + 1
            return f"In {days} day{'s' if days > 1 else ''}"
    
    def _reset_daily_limits(self):
        """Reset daily counters"""
        today = datetime.now().date().isoformat()
        if self.activity["last_reset"] != today:
            self.activity["last_reset"] = today
            self.activity["daily_connections"] = 0
            self.activity["daily_messages"] = 0
            self._save_json(self.activity_file, self.activity)
    
    def generate_campaign_report(self, campaign_id: str = None) -> str:
        """Generate detailed campaign performance report"""
        
        if campaign_id:
            campaigns_to_report = [c for c in self.campaigns if c["id"] == campaign_id]
        else:
            campaigns_to_report = self.campaigns
        
        report = f"""
# LinkedIn Networking Campaign Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overall Statistics
- Total Connections Sent: {self.activity['total_connections']}
- Response Rate: {self.activity['response_rate']:.1f}%
- Daily Limit: {self.activity['daily_connections']}/{self.DAILY_CONNECTION_LIMIT}
- Weekly Progress: {self.activity['weekly_connections']}/{self.WEEKLY_CONNECTION_LIMIT}

## Industry Breakdown
"""
        
        for industry, count in self.activity["industry_breakdown"].items():
            percentage = (count / self.activity['total_connections'] * 100) if self.activity['total_connections'] > 0 else 0
            report += f"- {industry.replace('_', ' ').title()}: {count} ({percentage:.1f}%)\n"
        
        report += "\n## Active Campaigns\n"
        
        for campaign in campaigns_to_report:
            if campaign["status"] != "active":
                continue
            
            stats = campaign["stats"]
            acceptance_rate = (stats['connections_accepted'] / stats['connections_sent'] * 100) if stats['connections_sent'] > 0 else 0
            response_rate = (stats['responses_received'] / stats['messages_sent'] * 100) if stats['messages_sent'] > 0 else 0
            
            report += f"""
### {campaign['name']} ({campaign['industry']})
- Connections Sent: {stats['connections_sent']}
- Acceptance Rate: {acceptance_rate:.1f}%
- Messages Sent: {stats['messages_sent']}
- Response Rate: {response_rate:.1f}%
- Meetings Scheduled: {stats['meetings_scheduled']}
- Target Companies: {', '.join(campaign['target_companies'][:5])}
"""
        
        # Pending connections by industry
        report += "\n## Pipeline Status\n"
        pending_by_industry = {}
        connected_by_industry = {}
        
        for target in self.targets:
            industry = target.get("industry", "unknown")
            if target["status"] == "pending":
                pending_by_industry[industry] = pending_by_industry.get(industry, 0) + 1
            elif target["status"] == "connected":
                connected_by_industry[industry] = connected_by_industry.get(industry, 0) + 1
        
        report += "\n### Pending Connections\n"
        for industry, count in pending_by_industry.items():
            report += f"- {industry.replace('_', ' ').title()}: {count}\n"
        
        report += "\n### Connected\n"
        for industry, count in connected_by_industry.items():
            report += f"- {industry.replace('_', ' ').title()}: {count}\n"
        
        # Active conversations
        active_convs = [c for c in self.conversations if c["status"] == "active"]
        report += f"\n## Active Conversations: {len(active_convs)}\n"
        
        return report

if __name__ == "__main__":
    import sys
    
    linkedin = AdvancedLinkedInNetworking()
    
    def print_menu():
        print("\n" + "="*60)
        print("LinkedIn Advanced Networking Automation")
        print("="*60)
        print("1.  Create Campaign")
        print("2.  Add Connection Target")
        print("3.  Get Daily Tasks")
        print("4.  Mark Connection Accepted")
        print("5.  Mark Connection Rejected")
        print("6.  Create Follow-up Sequence")
        print("7.  Record Message Sent")
        print("8.  Record Response Received")
        print("9.  Record Meeting Scheduled")
        print("10. View Campaign Report")
        print("11. List All Targets")
        print("12. List Active Campaigns")
        print("0.  Exit")
        print("="*60)
    
    def create_campaign_interactive():
        print("\n--- Create New Campaign ---")
        name = input("Campaign name: ")
        print("\nAvailable industries:")
        print("1. data_science_ai")
        print("2. finance")
        print("3. trading")
        industry_choice = input("Choose industry (1-3): ")
        
        industries = ["data_science_ai", "finance", "trading"]
        industry = industries[int(industry_choice) - 1]
        
        daily_target = input("Daily connection target (default 3): ") or "3"
        
        result = linkedin.create_targeted_campaign(
            campaign_name=name,
            industry=industry,
            daily_target=int(daily_target)
        )
        
        print(json.dumps(result, indent=2))
        return result.get("campaign_id")
    
    def add_target_interactive():
        print("\n--- Add Connection Target ---")
        
        # List active campaigns
        active_campaigns = [c for c in linkedin.campaigns if c["status"] == "active"]
        if active_campaigns:
            print("\nActive Campaigns:")
            for i, camp in enumerate(active_campaigns, 1):
                print(f"{i}. {camp['name']} ({camp['industry']})")
            campaign_choice = input("\nSelect campaign (number) or press Enter to skip: ")
            campaign_id = active_campaigns[int(campaign_choice) - 1]["id"] if campaign_choice else None
        else:
            campaign_id = None
        
        profile_url = input("LinkedIn profile URL: ")
        name = input("Full name: ")
        company = input("Company: ")
        position = input("Position/Title: ")
        
        print("\nAvailable industries:")
        print("1. data_science_ai")
        print("2. finance")
        print("3. trading")
        industry_choice = input("Choose industry (1-3): ")
        industries = ["data_science_ai", "finance", "trading"]
        industry = industries[int(industry_choice) - 1]
        
        print("\nPriority levels:")
        print("1. high")
        print("2. medium")
        print("3. low")
        priority_choice = input("Choose priority (default 2): ") or "2"
        priorities = ["high", "medium", "low"]
        priority = priorities[int(priority_choice) - 1]
        
        mutual = input("Mutual connections (default 0): ") or "0"
        
        result = linkedin.add_connection_target(
            profile_url=profile_url,
            name=name,
            company=company,
            position=position,
            industry=industry,
            campaign_id=campaign_id,
            priority=priority,
            mutual_connections=int(mutual)
        )
        
        print(json.dumps(result, indent=2))
    
    def list_targets():
        print("\n--- All Targets ---")
        if not linkedin.targets:
            print("No targets found.")
            return
        
        for i, target in enumerate(linkedin.targets, 1):
            print(f"\n{i}. {target['name']} - {target['company']}")
            print(f"   ID: {target['id']}")
            print(f"   Position: {target['position']}")
            print(f"   Status: {target['status']}")
            print(f"   Industry: {target['industry']}")
            print(f"   Priority: {target['priority']}")
    
    def mark_accepted_interactive():
        list_targets()
        target_num = input("\nEnter target number to mark as accepted: ")
        if target_num.isdigit() and 1 <= int(target_num) <= len(linkedin.targets):
            target = linkedin.targets[int(target_num) - 1]
            result = linkedin.mark_connection_accepted(target["id"])
            print(json.dumps(result, indent=2))
    
    def mark_rejected_interactive():
        list_targets()
        target_num = input("\nEnter target number to mark as rejected: ")
        if target_num.isdigit() and 1 <= int(target_num) <= len(linkedin.targets):
            target = linkedin.targets[int(target_num) - 1]
            result = linkedin.mark_connection_rejected(target["id"])
            print(json.dumps(result, indent=2))
    
    def create_followup_interactive():
        connected = [t for t in linkedin.targets if t["status"] == "connected"]
        if not connected:
            print("No connected targets found.")
            return
        
        print("\n--- Connected Targets ---")
        for i, target in enumerate(connected, 1):
            print(f"{i}. {target['name']} - {target['company']}")
        
        choice = input("\nSelect target for follow-up sequence: ")
        if choice.isdigit() and 1 <= int(choice) <= len(connected):
            target = connected[int(choice) - 1]
            result = linkedin.create_follow_up_sequence(target["id"])
            print(json.dumps(result, indent=2))
    
    def record_message_interactive():
        active_convs = [c for c in linkedin.conversations if c["status"] in ["active", "engaged"]]
        if not active_convs:
            print("No active conversations found.")
            return
        
        print("\n--- Active Conversations ---")
        for i, conv in enumerate(active_convs, 1):
            print(f"{i}. {conv['name']} - {conv['company']}")
            print(f"   Step: {conv['current_step']}/{len(conv['sequence'])}")
        
        choice = input("\nSelect conversation: ")
        if choice.isdigit() and 1 <= int(choice) <= len(active_convs):
            conv = active_convs[int(choice) - 1]
            result = linkedin.record_message_sent(conv["id"])
            print(json.dumps(result, indent=2))
    
    def record_response_interactive():
        list_targets()
        target_num = input("\nEnter target number who responded: ")
        if target_num.isdigit() and 1 <= int(target_num) <= len(linkedin.targets):
            target = linkedin.targets[int(target_num) - 1]
            response = input("Response text (optional): ")
            result = linkedin.record_response_received(target["id"], response if response else None)
            print(json.dumps(result, indent=2))
    
    def record_meeting_interactive():
        list_targets()
        target_num = input("\nEnter target number for meeting: ")
        if target_num.isdigit() and 1 <= int(target_num) <= len(linkedin.targets):
            target = linkedin.targets[int(target_num) - 1]
            meeting_date = input("Meeting date (YYYY-MM-DD): ")
            meeting_type = input("Meeting type (informational/interview/other): ") or "informational"
            result = linkedin.record_meeting_scheduled(target["id"], meeting_date, meeting_type)
            print(json.dumps(result, indent=2))
    
    def list_campaigns():
        print("\n--- All Campaigns ---")
        if not linkedin.campaigns:
            print("No campaigns found.")
            return
        
        for camp in linkedin.campaigns:
            print(f"\n{camp['name']} ({camp['status']})")
            print(f"  ID: {camp['id']}")
            print(f"  Industry: {camp['industry']}")
            print(f"  Stats: {json.dumps(camp['stats'], indent=4)}")
    
    # Interactive menu
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        # Run example mode
        print("Running example mode...")
        
        ai_campaign = linkedin.create_targeted_campaign(
            campaign_name="AI/ML Engineer Outreach",
            industry="data_science_ai",
            target_level="mid_senior",
            daily_target=3
        )
        print(json.dumps(ai_campaign, indent=2))
        
        result = linkedin.add_connection_target(
            profile_url="https://linkedin.com/in/example",
            name="Jane Doe",
            company="OpenAI",
            position="Machine Learning Engineer",
            industry="data_science_ai",
            campaign_id=ai_campaign["campaign_id"],
            priority="high",
            mutual_connections=2
        )
        print(json.dumps(result, indent=2))
        
        tasks = linkedin.get_daily_tasks()
        print(json.dumps(tasks, indent=2))
        
        report = linkedin.generate_campaign_report()
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
                create_campaign_interactive()
            elif choice == "2":
                add_target_interactive()
            elif choice == "3":
                tasks = linkedin.get_daily_tasks()
                print(json.dumps(tasks, indent=2))
            elif choice == "4":
                mark_accepted_interactive()
            elif choice == "5":
                mark_rejected_interactive()
            elif choice == "6":
                create_followup_interactive()
            elif choice == "7":
                record_message_interactive()
            elif choice == "8":
                record_response_interactive()
            elif choice == "9":
                record_meeting_interactive()
            elif choice == "10":
                report = linkedin.generate_campaign_report()
                print(report)
            elif choice == "11":
                list_targets()
            elif choice == "12":
                list_campaigns()
            else:
                print("Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")
