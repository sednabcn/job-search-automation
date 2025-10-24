#!/usr/bin/env python3
import json
from pathlib import Path

def main():
    print("\n" + "="*80)
    print("🎯 PHASE 2-ENABLED PIPELINE SUMMARY")
    print("="*80)
    
    # Load scored jobs if available
    scored_file = Path('job_search/scored_jobs.json')
    if scored_file.exists():
        try:
            with open(scored_file) as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, dict):
                scored_jobs = data.get('jobs', []) or data.get('scored_jobs', [])
            elif isinstance(data, list):
                scored_jobs = data
            else:
                scored_jobs = []
            
            # Process jobs...
            if scored_jobs and isinstance(scored_jobs, list):
                high_quality = len([j for j in scored_jobs if isinstance(j, dict) and j.get('score', 0) >= 70])
                valid_scores = [j.get('score', 0) for j in scored_jobs if isinstance(j, dict) and 'score' in j]
                
                if valid_scores:
                    avg_score = sum(valid_scores) / len(valid_scores)
                    print(f"\n🎯 JOB SCORING:")
                    print(f"   Total scored: {len(scored_jobs)}")
                    print(f"   High quality (≥70): {high_quality}")
                    print(f"   Average score: {avg_score:.1f}")
        except Exception as e:
            print(f"\n⚠️ Error processing scored jobs: {e}")
    
    # Load cover letters
    cover_letters_dir = Path('job_search/cover_letters')
    if cover_letters_dir.exists():
        letter_count = len(list(cover_letters_dir.glob('*.txt')))
        print(f"\n📝 AI COVER LETTERS:")
        print(f"   Generated: {letter_count}")
    
    # Load packages
    packages_dir = Path('job_search/application_packages')
    if packages_dir.exists():
        package_count = len(list(packages_dir.glob('app_*')))
        print(f"\n📦 APPLICATION PACKAGES:")
        print(f"   Created: {package_count}")
    
    print("="*80)

if __name__ == '__main__':
    main()
