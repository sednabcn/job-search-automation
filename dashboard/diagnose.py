# diagnose.py
import json
import yaml
from pathlib import Path

def diagnose():
    issues = []
    
    # Check files
    if not Path('job-manager-config.yml').exists():
        issues.append("❌ job-manager-config.yml missing")
    
    if not Path('keyword_analysis_report.json').exists():
        issues.append("❌ keyword_analysis_report.json missing")
    
    # Validate YAML
    try:
        with open('job-manager-config.yml') as f:
            yaml.safe_load(f)
    except Exception as e:
        issues.append(f"❌ Invalid YAML: {e}")
    
    # Check keyword counts
    try:
        with open('keyword_analysis_report.json') as f:
            report = json.load(f)
            if not report.get('keyword_analysis'):
                issues.append("⚠️ No keywords extracted")
    except Exception as e:
        issues.append(f"❌ Invalid report JSON: {e}")
    
    if not issues:
        print("✅ All checks passed")
    else:
        for issue in issues:
            print(issue)

if __name__ == '__main__':
    diagnose()
