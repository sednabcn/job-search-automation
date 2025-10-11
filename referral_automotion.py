#!/usr/bin/env python3
"""
Referral Automation System - Smart Referral Request & Relationship Building
Manages referral pipeline with relationship warmth tracking
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

class RelationshipStage(Enum):
    COLD = "cold"  # Just connected
    WARMING = "warming"  # 1-2 interactions
    WARM = "warm"  # 3-5 interactions, can ask light favors
    STRONG = "strong"  # 6+ interactions, established relationship
    REFERRAL_READY = "referral_ready"  # Ready to ask for referral

class InteractionType(Enum):
    CONNECTION = "connection"
    COFFEE_CHAT = "coffee_chat"
    VALUE_GIVEN = "value_given"
    CASUAL_MESSAGE = "casual_message"
    SHARED_CONTENT = "shared_content"
    INTRODUCTION_MADE = "introduction_made"

class ReferralAutomation:
    def __init__(self, data_dir: str = "job_search"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Data files
        self.relationships_file = self.data_dir / "referral_relationships.json"
        self.pipeline_file = self.data_dir / "referral_pipeline.json"
        self.requests_file = self.data_dir / "referral_requests.json"
        
        self.relationships = self._load_json(self.relationships_file, [])
        self.pipeline = self._load_json(self.pipeline_file, self._default_pipeline())
        self.requests = self._load_json(self.requests_file, [])
        
        # Relationship building rules
        self.INTERACTION_POINTS = {
            "connection": 1,
            "coffee_chat": 3,
            "value_given": 2,
            "casual_message": 1,
            "shared_content": 1,
            "introduction_made": 3
        }
        
        self.STAGE_THRESHOLDS = {
            "cold": 0,
            "warming": 2,
            "warm": 5,
            "strong": 10,
            "referral_ready": 15
        }
    
    def _load_json(self, filepath: Path, default):
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, filepath: Path, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _default_pipeline(self):
        return {
            "target_companies": [],
            "warming_queue": [],
            "ready_for_referral": [],
            "referral_requested": []
        }
    
    def add_relationship(self, name: str, company: str, position: str,
                        linkedin_url: str, connection_context: str) -> str:
        """Add new relationship to track"""
        
        relationship_id = f"REL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        relationship = {
            "id": relationship_id,
            "name": name,
            "company": company,
            "position": position,
            "linkedin_url": linkedin_url,
            "connection_context": connection_context,
            "stage": "cold",
            "interaction_points": 1,  # Connection counts as 1 point
            "interactions": [{
                "type": "connection",
                "date": datetime.now().isoformat(),
                "notes": connection_context
            }],
            "last_interaction": datetime.now().isoformat(),
            "next_interaction": (datetime.now() + timedelta(days=7)).isoformat(),
            "can_ask_referral": False,
            "target_company_match": False,
            "value_provided": [],
            "created_date": datetime.now().isoformat()
        }
        
        self.relationships.append(relationship)
        self._save_json(self.relationships_file, self.relationships)
        
        return relationship_id
    
    def log_interaction(self, relationship_id: str, interaction_type: str,
                       notes: str = "", value_provided: str = "") -> Dict:
        """Log interaction and update relationship stage"""
        
        relationship = self._get_relationship(relationship_id)
        if not relationship:
            return {"success": False, "error": "Relationship not found"}
        
        # Add interaction
        points = self.INTERACTION_POINTS.get(interaction_type, 1)
        
        interaction = {
            "type": interaction_type,
            "date": datetime.now().isoformat(),
            "notes": notes,
            "points": points
        }
        
        relationship["interactions"].append(interaction)
        relationship["interaction_points"] += points
        relationship["last_interaction"] = datetime.now().isoformat()
        
        # Track value provided
        if value_provided:
            relationship["value_provided"].append({
                "date": datetime.now().isoformat(),
                "value": value_provided
            })
        
        # Update stage
        old_stage = relationship["stage"]
        relationship["stage"] = self._calculate_stage(relationship["interaction_points"])
        
        # Update referral readiness
        relationship["can_ask_referral"] = (
            relationship["stage"] in ["warm", "strong", "referral_ready"] and
            relationship["interaction_points"] >= self.STAGE_THRESHOLDS["warm"]
        )
        
        # Schedule next interaction
        relationship["next_interaction"] = self._schedule_next_interaction(
            relationship["stage"],
            interaction_type
        )
        
        self._update_relationship(relationship)
        
        return {
            "success": True,
            "old_stage": old_stage,
            "new_stage": relationship["stage"],
            "interaction_points": relationship["interaction_points"],
            "can_ask_referral": relationship["can_ask_referral"],
            "next_interaction": relationship["next_interaction"]
        }
    
    def _calculate_stage(self, points: int) -> str:
        """Calculate relationship stage based on interaction points"""
        
        if points >= self.STAGE_THRESHOLDS["referral_ready"]:
            return "referral_ready"
        elif points >= self.STAGE_THRESHOLDS["strong"]:
            return "strong"
        elif points >= self.STAGE_THRESHOLDS["warm"]:
            return "warm"
        elif points >= self.STAGE_THRESHOLDS["warming"]:
            return "warming"
        else:
            return "cold"
    
    def _schedule_next_interaction(self, stage: str, last_interaction_type: str) -> str:
        """Schedule next interaction based on relationship stage"""
        
        # Interaction cadence by stage
        cadence = {
            "cold": 7,  # Week after connection
            "warming": 14,  # Every 2 weeks
            "warm": 21,  # Every 3 weeks
            "strong": 30,  # Monthly
            "referral_ready": 7  # Weekly until referral asked
        }
        
        days = cadence.get(stage, 14)
        return (datetime.now() + timedelta(days=days)).isoformat()
    
    def add_target_company(self, company_name: str, priority: str = "medium",
                          specific_roles: List[str] = None) -> Dict:
        """Add company to target list for referral pipeline"""
        
        target = {
            "id": f"TARGET-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "company": company_name,
            "priority": priority,
            "specific_roles": specific_roles or [],
            "employees_connected": [],
            "referrals_requested": 0,
            "referrals_received": 0,
            "added_date": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.pipeline["target_companies"].append(target)
        self._save_json(self.pipeline_file, self.pipeline)
        
        # Match existing relationships to this target
        self._match_relationships_to_target(company_name)
        
        return {
            "success": True,
            "target_id": target["id"],
            "matched_connections": len([r for r in self.relationships if r["company"] == company_name])
        }
    
    def _match_relationships_to_target(self, company_name: str):
        """Match existing relationships to target company"""
        
        for relationship in self.relationships:
            if relationship["company"].lower() == company_name.lower():
                relationship["target_company_match"] = True
        
        self._save_json(self.relationships_file, self.relationships)
    
    def get_referral_candidates(self, company: str = None) -> List[Dict]:
        """Get relationships ready for referral requests"""
        
        candidates = []
        
        for relationship in self.relationships:
            # Filter by company if specified
            if company and relationship["company"].lower() != company.lower():
                continue
            
            # Must be referral-ready
            if not relationship["can_ask_referral"]:
                continue
            
            # Must not have active referral request
            active_requests = [r for r in self.requests 
                             if r["relationship_id"] == relationship["id"] 
                             and r["status"] in ["pending", "active"]]
            
            if active_requests:
                continue
            
            candidates.append({
                "relationship_id": relationship["id"],
                "name": relationship["name"],
                "company": relationship["company"],
                "position": relationship["position"],
                "stage": relationship["stage"],
                "interaction_points": relationship["interaction_points"],
                "last_interaction": relationship["last_interaction"],
                "value_provided_count": len(relationship["value_provided"]),
                "target_company_match": relationship["target_company_match"]
            })
        
        # Sort by interaction points and target match
        candidates.sort(key=lambda x: (
            x["target_company_match"],
            x["interaction_points"]
        ), reverse=True)
        
        return candidates
    
    def request_referral(self, relationship_id: str, job_url: str,
                        job_title: str, why_good_fit: str) -> Dict:
        """Request referral from relationship"""
        
        relationship = self._get_relationship(relationship_id)
        if not relationship:
            return {"success": False, "error": "Relationship not found"}
        
        if not relationship["can_ask_referral"]:
            return {
                "success": False,
                "error": f"Relationship not ready (stage: {relationship['stage']}, points: {relationship['interaction_points']})",
                "recommendation": "Build more rapport before asking for referral"
            }
        
        # Generate personalized referral request
        message = self._generate_referral_request(
            relationship["name"],
            relationship["company"],
            job_title,
            why_good_fit,
            relationship["value_provided"]
        )
        
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        referral_request = {
            "id": request_id,
            "relationship_id": relationship_id,
            "contact_name": relationship["name"],
            "company": relationship["company"],
            "job_url": job_url,
            "job_title": job_title,
            "why_good_fit": why_good_fit,
            "message": message,
            "request_date": datetime.now().isoformat(),
            "status": "pending",
            "response_date": None,
            "outcome": None,
            "follow_up_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        self.requests.append(referral_request)
        self._save_json(self.requests_file, self.requests)
        
        return {
            "success": True,
            "request_id": request_id,
            "message": message,
            "next_steps": "Send this message to the contact and log the response"
        }
    
    def _generate_referral_request(self, name: str, company: str,
                                   job_title: str, why_good_fit: str,
                                   value_provided: List) -> str:
        """Generate personalized referral request message"""
        
        first_name = name.split()[0]
        
        # Reference value provided if any
        value_reference = ""
        if value_provided:
            recent_value = value_provided[-1]["value"]
            value_reference = f"\n\nI remember you mentioned {recent_value}, and I hope that was helpful. "
        
        message = f"""Hi {first_name},

I hope you're doing well! I've really enjoyed our conversations about {company} and learning from your experience there.{value_reference}

I wanted to reach out because I came across an opening for {job_title} at {company} that seems like a perfect match for my background. {why_good_fit}

Would you be comfortable providing a referral or sharing insights about the team and application process? I completely understand if timing isn't right, and I appreciate any guidance you can offer.

Thanks so much for considering!

Best regards"""
        
        return message
    
    def update_referral_status(self, request_id: str, status: str,
                               outcome: str = None, notes: str = "") -> Dict:
        """Update referral request status"""
        
        request = self._get_request(request_id)
        if not request:
            return {"success": False, "error": "Request not found"}
        
        request["status"] = status
        request["response_date"] = datetime.now().isoformat()
        
        if outcome:
            request["outcome"] = outcome
        
        if notes:
            request["notes"] = notes
        
        # If accepted, log as strong interaction
        if status == "accepted":
            self.log_interaction(
                request["relationship_id"],
                "introduction_made",
                f"Provided referral for {request['job_title']}"
            )
        
        self._save_json(self.requests_file, self.requests)
        
        return {"success": True, "updated_status": status}
    
    def get_warming_queue(self) -> List[Dict]:
        """Get relationships that need interaction to warm up"""
        
        today = datetime.now().date().isoformat()
        warming = []
        
        for relationship in self.relationships:
            # Skip if already referral-ready
            if relationship["can_ask_referral"]:
                continue
            
            # Check if interaction is due
            if relationship["next_interaction"][:10] <= today:
                warming.append({
                    "relationship_id": relationship["id"],
                    "name": relationship["name"],
                    "company": relationship["company"],
                    "stage": relationship["stage"],
                    "interaction_points": relationship["interaction_points"],
                    "points_to_next_stage": self._points_to_next_stage(relationship["interaction_points"]),
                    "last_interaction": relationship["last_interaction"],
                    "suggested_action": self._suggest_next_action(relationship),
                    "target_company_match": relationship["target_company_match"]
                })
        
        # Sort by target match and stage
        warming.sort(key=lambda x: (x["target_company_match"], x["interaction_points"]), reverse=True)
        
        return warming
    
    def _points_to_next_stage(self, current_points: int) -> int:
        """Calculate points needed for next stage"""
        
        for stage, threshold in sorted(self.STAGE_THRESHOLDS.items(), key=lambda x: x[1]):
            if current_points < threshold:
                return threshold - current_points
        return 0
    
    def _suggest_next_action(self, relationship: Dict) -> str:
        """Suggest next interaction based on relationship stage and history"""
        
        stage = relationship["stage"]
        last_interactions = [i["type"] for i in relationship["interactions"][-3:]]
        
        suggestions = {
            "cold": [
                "Send casual message asking about their experience",
                "Share relevant article about their industry",
                "Comment on their recent LinkedIn post"
            ],
            "warming": [
                "Propose 15-min coffee chat",
                "Share valuable resource related to their work",
                "Ask for advice on industry topic"
            ],
            "warm": [
                "Make introduction to someone in your network",
                "Share job posting that might interest them",
                "Invite to virtual event or webinar"
            ],
            "strong": [
                "Check in on how they're doing",
                "Share major career update",
                "Offer help with something they mentioned"
            ]
        }
        
        # Avoid repeating same interaction type
        available_suggestions = suggestions.get(stage, suggestions["warming"])
        return available_suggestions[0]  # Could be smarter here
    
    def _get_relationship(self, relationship_id: str) -> Optional[Dict]:
        """Get relationship by ID"""
        for rel in self.relationships:
            if rel["id"] == relationship_id:
                return rel
        return None
    
    def _update_relationship(self, relationship: Dict):
        """Update relationship in storage"""
        for i, rel in enumerate(self.relationships):
            if rel["id"] == relationship["id"]:
                self.relationships[i] = relationship
                break
        self._save_json(self.relationships_file, self.relationships)
    
    def _get_request(self, request_id: str) -> Optional[Dict]:
        """Get referral request by ID"""
        for req in self.requests:
            if req["id"] == request_id:
                return req
        return None
    
    def generate_pipeline_report(self) -> str:
        """Generate referral pipeline report"""
        
        candidates = self.get_referral_candidates()
        warming = self.get_warming_queue()
        
        # Statistics
        total_relationships = len(self.relationships)
        by_stage = {}
        for rel in self.relationships:
            stage = rel["stage"]
            by_stage[stage] = by_stage.get(stage, 0) + 1
        
        active_requests = len([r for r in self.requests if r["status"] in ["pending", "active"]])
        successful_referrals = len([r for r in self.requests if r["outcome"] == "accepted"])
        
        report = f"""
# Referral Pipeline Report - {datetime.now().strftime('%Y-%m-%d')}

## Network Overview
- Total Relationships: {total_relationships}
- Cold: {by_stage.get('cold', 0)}
- Warming: {by_stage.get('warming', 0)}
- Warm: {by_stage.get('warm', 0)}
- Strong: {by_stage.get('strong', 0)}
- Referral Ready: {by_stage.get('referral_ready', 0)}

## Referral Statistics
- Active Requests: {active_requests}
- Successful Referrals: {successful_referrals}
- Success Rate: {(successful_referrals / len(self.requests) * 100) if self.requests else 0:.1f}%

## Ready for Referral ({len(candidates)})
"""
        
        if candidates:
            for candidate in candidates[:5]:  # Top 5
                report += f"\n### {candidate['name']} - {candidate['company']}\n"
                report += f"- Stage: {candidate['stage']} ({candidate['interaction_points']} points)\n"
                report += f"- Last Interaction: {candidate['last_interaction'][:10]}\n"
                report += f"- Value Provided: {candidate['value_provided_count']} times\n"
                if candidate['target_company_match']:
                    report += f"- ⭐ TARGET COMPANY MATCH\n"
        else:
            report += "\nNo relationships ready for referral yet. Keep building rapport!\n"
        
        report += f"\n## Warming Queue ({len(warming)})\n"
        
        if warming:
            for rel in warming[:5]:  # Top 5
                report += f"\n### {rel['name']} - {rel['company']}\n"
                report += f"- Stage: {rel['stage']} ({rel['interaction_points']} points)\n"
                report += f"- Points to Next Stage: {rel['points_to_next_stage']}\n"
                report += f"- Suggested Action: {rel['suggested_action']}\n"
        
        report += f"\n## Target Companies ({len(self.pipeline['target_companies'])})\n"
        
        for target in self.pipeline['target_companies']:
            connections = len([r for r in self.relationships if r['company'] == target['company']])
            report += f"\n- {target['company']} (Priority: {target['priority']})\n"
            report += f"  Connections: {connections}, Referrals Requested: {target['referrals_requested']}\n"
        
        return report
    
    def get_daily_actions(self) -> Dict:
        """Get today's recommended referral actions"""
        
        return {
            "warming_interactions": self.get_warming_queue()[:3],  # Top 3 to warm up
            "ready_for_referral": self.get_referral_candidates()[:2],  # Top 2 ready
            "follow_ups_due": self._get_follow_ups_due(),
            "recommendations": self._get_daily_recommendations()
        }
    
    def _get_follow_ups_due(self) -> List[Dict]:
        """Get referral requests needing follow-up"""
        
        today = datetime.now().date().isoformat()
        follow_ups = []
        
        for request in self.requests:
            if request["status"] == "pending" and request["follow_up_date"][:10] <= today:
                follow_ups.append({
                    "request_id": request["id"],
                    "contact_name": request["contact_name"],
                    "company": request["company"],
                    "job_title": request["job_title"],
                    "request_date": request["request_date"][:10],
                    "days_pending": (datetime.now().date() - datetime.fromisoformat(request["request_date"][:10])).days
                })
        
        return follow_ups
    
    def _get_daily_recommendations(self) -> List[str]:
        """Get personalized daily recommendations"""
        
        recommendations = []
        
        # Check if we have enough warm relationships
        warm_count = len([r for r in self.relationships if r["stage"] in ["warm", "strong", "referral_ready"]])
        if warm_count < 5:
            recommendations.append("Focus on warming up more relationships before requesting referrals (target: 5+ warm connections)")
        
        # Check target company coverage
        target_companies = self.pipeline["target_companies"]
        for target in target_companies:
            connections = len([r for r in self.relationships if r["company"] == target["company"]])
            if connections == 0:
                recommendations.append(f"Find and connect with employees at {target['company']}")
            elif connections < 3:
                recommendations.append(f"Build more connections at {target['company']} (current: {connections})")
        
        # Check for stale relationships
        stale = [r for r in self.relationships 
                if (datetime.now() - datetime.fromisoformat(r["last_interaction"])).days > 60]
        if stale:
            recommendations.append(f"Re-engage with {len(stale)} relationships that have gone cold")
        
        # Check follow-up rate
        active_requests = [r for r in self.requests if r["status"] == "pending"]
        if len(active_requests) > 3:
            recommendations.append("Follow up on pending referral requests before making new ones")
        
        return recommendations if recommendations else ["Keep building relationships! You're on track."]


if __name__ == "__main__":
    # Example usage
    referral_system = ReferralAutomation()
    
    # Add relationship
    rel_id = referral_system.add_relationship(
        name="John Doe",
        company="Tech Corp",
        position="Senior Engineer",
        linkedin_url="https://linkedin.com/in/johndoe",
        connection_context="Met at tech conference"
    )
    
    # Log interaction
    result = referral_system.log_interaction(
        relationship_id=rel_id,
        interaction_type="coffee_chat",
        notes="Had great 30-min call about their team",
        value_provided="Shared article on ML optimization"
    )
    
    print(json.dumps(result, indent=2))
    
    # Generate report
    report = referral_system.generate_pipeline_report()
    print(report)
