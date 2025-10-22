#!/usr/bin/env python3
"""
Configuration file validator for job-manager-config.yml
Validates structure and provides helpful error messages
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class ConfigValidator:
    """Validate job search configuration file"""
    
    # Required sections (must be present)
    REQUIRED_SECTIONS = ['platforms', 'search']
    
    # Optional sections (nice to have but not required)
    OPTIONAL_SECTIONS = ['matching', 'generated_at', 'metadata', 'notifications']
    
    # Required platform fields
    REQUIRED_PLATFORM_FIELDS = ['max_results_per_search']
    
    # Valid status values for application tracking
    VALID_STATUSES = ['applied', 'viewed', 'phone_screen', 'interview', 'offer', 'rejected', 'ghosted']
    
    def __init__(self, config_path: str = 'job-manager-config.yml'):
        self.config_path = Path(config_path)
        self.config = None
        self.errors = []
        self.warnings = []
    
    def load_config(self) -> bool:
        """Load and parse the config file"""
        if not self.config_path.exists():
            self.errors.append(f"Config file not found: {self.config_path}")
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            if self.config is None:
                self.errors.append("Config file is empty")
                return False
            
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading config: {e}")
            return False
    
    def validate_structure(self) -> bool:
        """Validate overall config structure"""
        if not isinstance(self.config, dict):
            self.errors.append("Config must be a dictionary")
            return False
        
        # Check required sections
        missing_required = [s for s in self.REQUIRED_SECTIONS if s not in self.config]
        if missing_required:
            self.errors.append(f"Missing required sections: {missing_required}")
            return False
        
        # Warn about missing optional sections
        missing_optional = [s for s in self.OPTIONAL_SECTIONS if s not in self.config]
        if missing_optional:
            self.warnings.append(f"Missing optional sections: {missing_optional}")
            self.warnings.append("These sections can be generated using 'extract-keywords' command")
        
        return True
    
    def validate_platforms(self) -> bool:
        """Validate platforms section"""
        platforms = self.config.get('platforms', {})
        
        if not isinstance(platforms, dict):
            self.errors.append("'platforms' must be a dictionary")
            return False
        
        if not platforms:
            self.warnings.append("No platforms configured")
            return True
        
        valid_platforms = ['linkedin', 'glassdoor', 'indeed', 'reed']
        
        for platform_name, platform_config in platforms.items():
            if platform_name not in valid_platforms:
                self.warnings.append(f"Unknown platform: {platform_name}")
            
            if not isinstance(platform_config, dict):
                self.errors.append(f"Platform '{platform_name}' config must be a dictionary")
                continue
            
            # Check required fields
            for field in self.REQUIRED_PLATFORM_FIELDS:
                if field not in platform_config:
                    self.errors.append(f"Platform '{platform_name}' missing required field: {field}")
            
            # Validate max_results_per_search
            if 'max_results_per_search' in platform_config:
                max_results = platform_config['max_results_per_search']
                if not isinstance(max_results, int) or max_results < 1:
                    self.errors.append(
                        f"Platform '{platform_name}': max_results_per_search must be positive integer"
                    )
        
        return len(self.errors) == 0
    
    def validate_search(self) -> bool:
        """Validate search section"""
        search = self.config.get('search', {})
        
        if not isinstance(search, dict):
            self.errors.append("'search' must be a dictionary")
            return False
        
        # Check for target_roles
        if 'target_roles' in search:
            roles = search['target_roles']
            if not isinstance(roles, list):
                self.errors.append("'search.target_roles' must be a list")
            elif not roles:
                self.warnings.append("'search.target_roles' is empty")
            else:
                # Validate each role is a string
                for i, role in enumerate(roles):
                    if not isinstance(role, str):
                        self.errors.append(f"search.target_roles[{i}] must be a string")
        else:
            self.warnings.append("No 'target_roles' defined in search section")
        
        # Check for default_location
        if 'default_location' in search:
            if not isinstance(search['default_location'], str):
                self.errors.append("'search.default_location' must be a string")
        else:
            self.warnings.append("No 'default_location' defined (will default to 'London')")
        
        return len(self.errors) == 0
    
    def validate_matching(self) -> bool:
        """Validate matching section (optional)"""
        if 'matching' not in self.config:
            return True  # Optional section
        
        matching = self.config['matching']
        
        if not isinstance(matching, dict):
            self.errors.append("'matching' must be a dictionary")
            return False
        
        # Validate keywords sections
        for category in ['required_keywords', 'preferred_keywords', 'excluded_keywords']:
            if category in matching:
                keywords = matching[category]
                if not isinstance(keywords, list):
                    self.errors.append(f"matching.{category} must be a list")
                else:
                    for i, keyword in enumerate(keywords):
                        if not isinstance(keyword, str):
                            self.errors.append(f"matching.{category}[{i}] must be a string")
        
        # Validate scoring weights
        if 'scoring_weights' in matching:
            weights = matching['scoring_weights']
            if not isinstance(weights, dict):
                self.errors.append("matching.scoring_weights must be a dictionary")
            else:
                for key, value in weights.items():
                    if not isinstance(value, (int, float)):
                        self.errors.append(
                            f"matching.scoring_weights.{key} must be a number"
                        )
        
        return len(self.errors) == 0
    
    def validate_all(self) -> bool:
        """Run all validations"""
        if not self.load_config():
            return False
        
        validations = [
            self.validate_structure(),
            self.validate_platforms(),
            self.validate_search(),
            self.validate_matching()
        ]
        
        return all(validations)
    
    def print_results(self, exit_on_error: bool = True) -> int:
        """Print validation results and optionally exit"""
        if not self.errors and not self.warnings:
            print("✅ Configuration is valid!")
            return 0
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
            
            if exit_on_error:
                print("\n💡 To fix configuration issues:")
                print("  1. Check the structure of job-manager-config.yml")
                print("  2. Run 'python job_search_cli.py extract-keywords --update-config'")
                print("     to generate missing optional sections")
                sys.exit(1)
            
            return 1
        
        return 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate job search configuration')
    parser.add_argument('--config', default='job-manager-config.yml',
                       help='Path to config file')
    parser.add_argument('--no-exit', action='store_true',
                       help='Do not exit on errors (for testing)')
    
    args = parser.parse_args()
    
    print(f"✅ Validating config file: {args.config}...")
    
    validator = ConfigValidator(args.config)
    validator.validate_all()
    
    return validator.print_results(exit_on_error=not args.no_exit)


if __name__ == "__main__":
    sys.exit(main())
