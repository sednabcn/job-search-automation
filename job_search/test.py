from pathlib import Path
from .github.scripts.professional_job_center_cli import KeywordExtractor
import sys

# Job positions
positions = ["Senior Software Engineer", "Tech Lead"]

# Job files
files = ["linkedin_jobs.json", "glassdoor_jobs.json", "indeed_jobs.json"]

# Initialize extractor
extractor = KeywordExtractor(positions)

# Load jobs
jobs = extractor.load_jobs_from_files(files)

# Analyze jobs (this populates analysis_results)
extractor.extract_keywords(jobs)

# Export analysis report (JSON)
extractor.export_analysis_report("job-manager-config.json")

# Generate YAML configuration
extractor.generate_config("job-manager-config-preview.yml")

print("✅ Jobs analyzed and config generated successfully")

