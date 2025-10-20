#!/usr/bin/env python3
"""
JSON File Updater for Job Search System
Adds new entries from JSON input to the appropriate tracking files
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class JobSearchJSONUpdater:
    def __init__(self, tracking_dir: str = "job_search"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.files = {
            "applications": self.tracking_dir / "applications.json",
            "contacts": self.tracking_dir / "network_contacts.json",
            "searches": self.tracking_dir / "saved_searches.json"
        }
        
        # Initialize files if they don't exist
        for file_path in self.files.values():
            if not file_path.exists():
                self._write_json(file_path, [])
    
    def _read_json(self, file_path: Path) -> List[Dict]:
        """Read JSON file safely"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_json(self, file_path: Path, data: List[Dict]) -> None:
        """Write JSON file with pretty formatting"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_application(self, app_data: Dict) -> Dict:
        """Add new application to applications.json"""
        applications = self._read_json(self.files["applications"])
        
        # Check for duplicates
        for app in applications:
            if app.get('company') == app_data.get('company') and \
               app.get('position') == app_data.get('position'):
                return {
                    "success": False,
                    "message": f"Application to {app_data['company']} for {app_data['position']} already exists",
                    "id": app.get('id')
                }
        
        # Add new application
        applications.append(app_data)
        self._write_json(self.files["applications"], applications)
        
        return {
            "success": True,
            "message": f"Added application to {app_data['company']}",
            "id": app_data.get('id'),
            "total_applications": len(applications)
        }
    
    def add_contact(self, contact_data: Dict) -> Dict:
        """Add new contact to network_contacts.json"""
        contacts = self._read_json(self.files["contacts"])
        
        # Check for duplicates
        for contact in contacts:
            if contact.get('name') == contact_data.get('name') and \
               contact.get('company') == contact_data.get('company'):
                return {
                    "success": False,
                    "message": f"Contact {contact_data['name']} at {contact_data.get('company', 'Unknown')} already exists",
                    "id": contact.get('id')
                }
        
        # Add new contact
        contacts.append(contact_data)
        self._write_json(self.files["contacts"], contacts)
        
        return {
            "success": True,
            "message": f"Added contact {contact_data['name']}",
            "id": contact_data.get('id'),
            "total_contacts": len(contacts)
        }
    
    def add_search(self, search_data: Dict) -> Dict:
        """Add new saved search to saved_searches.json"""
        searches = self._read_json(self.files["searches"])
        
        # Check for duplicates
        for search in searches:
            if search.get('name') == search_data.get('name'):
                return {
                    "success": False,
                    "message": f"Search '{search_data['name']}' already exists",
                    "id": search.get('id')
                }
        
        # Add new search
        searches.append(search_data)
        self._write_json(self.files["searches"], searches)
        
        return {
            "success": True,
            "message": f"Added saved search '{search_data['name']}'",
            "id": search_data.get('id'),
            "total_searches": len(searches)
        }
    
    def process_input(self, input_json: str, data_type: str) -> Dict:
        """Process JSON input and add to appropriate file"""
        try:
            data = json.loads(input_json)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"Invalid JSON: {str(e)}"
            }
        
        if data_type == "application":
            return self.add_application(data)
        elif data_type == "contact":
            return self.add_contact(data)
        elif data_type == "search":
            return self.add_search(data)
        else:
            return {
                "success": False,
                "message": f"Unknown data type: {data_type}"
            }
    
    def get_summary(self) -> Dict:
        """Get summary of all tracked data"""
        applications = self._read_json(self.files["applications"])
        contacts = self._read_json(self.files["contacts"])
        searches = self._read_json(self.files["searches"])
        
        # Application statistics
        app_stats = {
            "total": len(applications),
            "by_status": {}
        }
        for app in applications:
            status = app.get("status", "unknown")
            app_stats["by_status"][status] = app_stats["by_status"].get(status, 0) + 1
        
        # Contact statistics
        contact_stats = {
            "total": len(contacts),
            "by_strength": {}
        }
        for contact in contacts:
            strength = contact.get("relationship_strength", "unknown")
            contact_stats["by_strength"][strength] = contact_stats["by_strength"].get(strength, 0) + 1
        
        return {
            "applications": app_stats,
            "contacts": contact_stats,
            "searches": {
                "total": len(searches)
            },
            "last_updated": datetime.now().isoformat()
        }


def main():
    """CLI interface for the updater - supports both old and new syntax"""
    
    # Check if using old syntax: script.py <type>
    # vs new syntax: script.py --type <type>
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
        # OLD SYNTAX: python script.py application
        print("ℹ️  Using legacy syntax (positional argument)", file=sys.stderr)
        data_type = sys.argv[1]
        json_input = sys.stdin.read()
        tracking_dir = "job_search"
        
        updater = JobSearchJSONUpdater(tracking_dir=tracking_dir)
        result = updater.process_input(json_input, data_type)
        
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["success"] else 1)
    
    # NEW SYNTAX: Use argparse
    import argparse
    
    parser = argparse.ArgumentParser(description="Update job search JSON files")
    parser.add_argument("--type", "-t", required=True, 
                       choices=["application", "contact", "search"],
                       help="Type of data to add")
    parser.add_argument("--json", "-j", 
                       help="JSON string to add")
    parser.add_argument("--file", "-f",
                       help="File containing JSON data")
    parser.add_argument("--summary", "-s", action="store_true",
                       help="Show summary of tracked data")
    parser.add_argument("--tracking-dir", default="job_search",
                       help="Directory for tracking files")
    
    args = parser.parse_args()
    
    updater = JobSearchJSONUpdater(tracking_dir=args.tracking_dir)
    
    if args.summary:
        summary = updater.get_summary()
        print(json.dumps(summary, indent=2))
        return
    
    # Get JSON input
    if args.json:
        json_input = args.json
    elif args.file:
        with open(args.file, 'r') as f:
            json_input = f.read()
    else:
        print("Reading JSON from stdin...", file=sys.stderr)
        json_input = sys.stdin.read()
    
    # Process input
    result = updater.process_input(json_input, args.type)
    
    # Print result
    print(json.dumps(result, indent=2))
    
    if result["success"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
