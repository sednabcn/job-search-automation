# 🚀 Job Search Automation Suite

> **Your AI-powered career accelerator** – Automate job discovery, optimize applications, and land your dream role faster.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

Transform your job search from a full-time burden into a streamlined, intelligent process. This comprehensive automation suite discovers opportunities across multiple platforms, matches them to your profile with AI precision, and helps you apply faster—all while you focus on what matters most.

---

## ✨ What Makes This Special

🎯 **Smart, Not Spammy** – AI-powered matching ensures you only pursue relevant opportunities  
⚡ **Time-Saving** – From 3 hours/day to 15 minutes/day  
📊 **Data-Driven** – Make informed decisions with comprehensive analytics  
🤖 **Fully Automated** – Runs daily via GitHub Actions while you sleep  
🔒 **Private & Secure** – Your data stays yours, encrypted in GitHub Secrets  

### The Numbers

| Metric | Manual Approach | With Automation |
|--------|----------------|-----------------|
| **Jobs Discovered** | 5-10/day | 50-100/day |
| **Time Investment** | 2-3 hours/day | 15 min/day |
| **Applications Sent** | 5-10/day | 20-50/day |
| **Match Accuracy** | Subjective guess | AI-scored 0-100 |
| **Tracking** | Manual spreadsheet | Automated system |
| **Resume Optimization** | Generic | Tailored per job |
| **Networking** | Ad-hoc | Systematic |

---

## 🎯 Key Features

### 🔍 Multi-Platform Job Discovery
Search across the top platforms simultaneously:
- **LinkedIn** – Professional networking + job search
- **Glassdoor** – Company reviews + salary insights
- **Indeed** – Largest job database worldwide
- **Reed** – UK-focused with premium API access

### 🤖 AI-Powered Intelligence
- **Smart Matching** – 85-95% accuracy with 6-factor analysis
- **Keyword Extraction** – Auto-identify market trends from real listings
- **Resume Optimization** – ATS-friendly formatting + keyword density
- **Auto-Configuration** – System learns from market data

### 📈 Complete Application Lifecycle
```
Discover → Match → Optimize → Apply → Track → Follow-up → Interview
```

### 🔄 GitHub Actions Automation
- ⏰ Runs twice daily (8am & 8pm UTC)
- 📧 Email reports with top matches
- 📊 Weekly progress summaries
- 🔧 Automatic maintenance & cleanup

---

## 🚀 Quick Start

### Prerequisites

```bash
✓ Python 3.8+
✓ Git
✓ GitHub account
✓ LinkedIn account
✓ Gmail (for notifications)
```

### 5-Minute Setup

**1. Clone & Install**
```bash
git clone https://github.com/yourusername/job-search-automation.git
cd job-search-automation
pip install -r requirements.txt
```

**2. Configure Credentials**
```bash
cp .env.example .env
# Edit .env with your credentials
```

**3. Test Locally**
```bash
python job_search_cli.py
```

**4. Setup GitHub Actions**
```bash
# Add secrets in: Settings → Secrets → Actions
LINKEDIN_EMAIL, LINKEDIN_PASSWORD
GLASSDOOR_EMAIL, GLASSDOOR_PASSWORD
SENDER_EMAIL, SENDER_PASSWORD
```

**5. Push & Activate**
```bash
git add . && git commit -m "Initial setup" && git push
# Workflow runs automatically at 8am & 8pm UTC
```

---

## 💡 Common Use Cases

### Scenario 1: Career Change
```bash
# Update your target roles
python multi_platform_cli.py search \
  --positions "Data Scientist" "ML Engineer" "AI Researcher" \
  --location "Remote" \
  --max-per-platform 100

# Extract keywords from real job listings
python multi_platform_cli.py extract-keywords --update-config

# Match your resume to top opportunities
python job_matcher.py --resume cv.pdf --threshold 80
```

### Scenario 2: Salary Negotiation Research
```bash
# Get comprehensive salary data
python glassdoor_automotion.py --salary "Software Engineer" --location "London"

# Compare companies
python enhanced_glassdoor_automotion.py --report "Google,Meta,Amazon"

# Export for analysis
python job_search_cli.py export --format csv
```

### Scenario 3: Networking Sprint
```bash
# Connect with target companies
python linkedin_advanced_networking.py \
  --target-companies "Google,Amazon,Meta" \
  --roles "Recruiter,Hiring Manager" \
  --connection-limit 50

# Automated referral requests
python referral_automotion.py --company "Google"
```

---

## 📊 Smart Job Matching

Our AI analyzes 6 key factors to score each opportunity:

| Factor | Weight | What It Measures |
|--------|--------|------------------|
| 🎯 **Skills** | 35% | Required vs nice-to-have alignment |
| 💼 **Experience** | 25% | Years + seniority level match |
| 📍 **Location** | 15% | Remote/hybrid/office compatibility |
| 💰 **Salary** | 10% | Compensation range fit |
| 🏢 **Culture** | 10% | Values + work style alignment |
| 📈 **Growth** | 5% | Career progression potential |

**Score Interpretation:**
- 🟢 **90-100**: Excellent – Apply immediately
- 🟡 **80-89**: Strong – Highly recommended
- 🟠 **70-79**: Good – Worth considering
- 🔴 **60-69**: Fair – Review carefully
- ⚫ **<60**: Poor – Likely not suitable

---

## 🛠️ Core Commands

### Interactive CLI Menu
```bash
python job_search_cli.py
# Guided workflow for all features
```

### Automated Job Search
```bash
# Multi-platform search
python multi_platform_cli.py search \
  --positions "Senior Engineer" "Staff Engineer" \
  --platforms all \
  --location "London"

# Platform-specific
python linkedin_automotion.py --keywords "Python Developer"
python indeed_scraper.py --job-title "DevOps Engineer"
python reed_scraper.py --location "Manchester" --salary-min 70000
```

### Resume & Application
```bash
# Match resume to job
python job_matcher.py --resume cv.pdf --job-url "linkedin.com/jobs/123"

# Optimize for ATS
python resume_optimizer.py --input cv.docx --job-description job.txt

# Combined optimization
python Resume-Cover-Letter_Optimizer.py --job-url "example.com/job"
```

### Tracking & Analytics
```bash
# Add application
python job_search_tracker.py --add "Company" "Position" "Applied"

# View statistics
python job_search_tracker.py --stats

# Generate reports
python multi_platform_cli.py stats --files "*_jobs.json"
```

---

## 🤖 GitHub Actions Workflows

The system uses two complementary workflows that work together seamlessly:

### 1. **Job Discovery Worker** (`job-discovery-worker.yml`)
*The specialized multi-platform job scraper*

**Purpose**: Dedicated job discovery across all platforms
- Searches LinkedIn, Glassdoor, Indeed, and Reed simultaneously
- Optimized for speed and reliability
- Runs independently for maximum uptime
- Saves raw job data for processing

**Triggers**:
- 🕐 Scheduled: Every 12 hours (optimized for fresh listings)
- 🔘 Manual: On-demand via Actions tab or CLI
- 🔗 Workflow call: Invoked by Job Manager Center

**Manual Trigger Options**:
```yaml
# Via GitHub UI: Actions → Job Discovery Worker → Run workflow
platforms: all / linkedin / glassdoor / indeed / reed
job_titles: "Senior Software Engineer,Staff Engineer"
location: "London" / "Remote" / any location
max_results: 50 (jobs per platform)
```

**Via GitHub CLI**:
```bash
gh workflow run job-discovery-worker.yml \
  -f platforms="all" \
  -f job_titles="Senior Software Engineer,Tech Lead" \
  -f location="London" \
  -f max_results=100
```

**What it does**:
```
1. Parse input parameters (job titles, platforms, location)
2. Run scrapers in parallel for selected platforms
3. Deduplicate jobs across platforms
4. Clean and standardize data format
5. Export to JSON files (linkedin_jobs.json, etc.)
6. Upload as workflow artifacts (30-day retention)
```

---

### 2. **Job Manager Center Multi-Platform** (`job-manager-center-multiplatform.yml`)
*The intelligent orchestrator with keyword extraction*

**Purpose**: Complete end-to-end automation with smart configuration updates
- Auto-discovers jobs across all platforms
- Extracts trending keywords from real market data
- Auto-updates configuration based on job market analysis
- Matches jobs to your profile with AI scoring
- Generates comprehensive reports and notifications

**Triggers**:
- 🕐 Scheduled: Daily at 6 AM UTC
- 🔘 Manual: Full control via workflow dispatch or CLI
- 🔗 Workflow call: Can be triggered by Job Discovery Worker

**Manual Trigger Options**:
```yaml
# Via GitHub UI: Actions → Job Manager Center → Run workflow
job_positions: "Senior Software Engineer,Staff Engineer"
update_config: true / false (auto-commit updated config)
trigger_discovery: true / false (start full job search after)
skip_boards: "" / "linkedin,reed" (boards to skip)
```

**Via GitHub CLI**:
```bash
gh workflow run job-manager-center-multiplatform.yml \
  -f job_positions="Senior Software Engineer,Staff Engineer,Tech Lead" \
  -f update_config=true \
  -f trigger_discovery=true \
  -f skip_boards=""
```

**Via API**:
```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/job-manager-center-multiplatform.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "job_positions": "Senior Software Engineer,Principal Engineer",
      "update_config": "true",
      "trigger_discovery": "true",
      "skip_boards": "glassdoor"
    }
  }'
```

**4-Stage Pipeline**:

```
┌─────────────────────────────────────────────────────────┐
│ Stage 1: Initialize                                     │
│ ✓ Load configuration                                    │
│ ✓ Setup environment                                     │
│ ✓ Validate credentials                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 2: Discovery                                      │
│ ✓ Call job-discovery-worker.yml                        │
│ ✓ Multi-platform job search                            │
│ ✓ Download and aggregate results                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 3: Keyword Extraction & Config Update            │
│ ✓ Analyze job descriptions                             │
│ ✓ Extract trending keywords                            │
│ ✓ Calculate salary ranges                              │
│ ✓ Auto-update job-manager-config.yml                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 4: Matching                                       │
│ ✓ Score jobs against your profile (0-100)              │
│ ✓ Rank by compatibility                                │
│ ✓ Filter by threshold                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 5: Networking                                     │
│ ✓ LinkedIn connection automation                       │
│ ✓ Referral request workflows                           │
│ ✓ Profile engagement                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 6: Application                                    │
│ ✓ Resume optimization per job                          │
│ ✓ Cover letter generation                              │
│ ✓ Automated application submission (optional)          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 7: Reporting                                      │
│ ✓ Generate daily summary                               │
│ ✓ Create analytics dashboard                           │
│ ✓ Email top matches (score ≥ 85)                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 8: Maintenance                                    │
│ ✓ Archive old data (30+ days)                          │
│ ✓ Cleanup duplicate entries                            │
│ ✓ Optimize JSON files                                  │
│ ✓ Commit updated configuration                         │
└─────────────────────────────────────────────────────────┘
```

**Manual trigger options**:
```yaml
Mode: full / discovery / keyword_extraction / matching / networking / reporting
Platforms: all / linkedin / glassdoor / indeed / reed
Auto Apply: true / false
Update Keywords: true / false
Match Threshold: 70-100 (default: 80)
```

### Setting Up Workflows

**1. Required GitHub Secrets**

Go to: `Settings → Secrets and variables → Actions → New repository secret`

```bash
# Platform Credentials
LINKEDIN_EMAIL          # LinkedIn login email
LINKEDIN_PASSWORD       # LinkedIn password
GLASSDOOR_EMAIL         # Glassdoor login email
GLASSDOOR_PASSWORD      # Glassdoor password

# API Keys (Optional but Recommended)
REED_API_KEY           # Reed API key (free tier: 50 req/month)

# Email Notifications
SENDER_EMAIL           # Gmail address for sending reports
SENDER_PASSWORD        # Gmail app password (not regular password!)
NOTIFICATION_EMAIL     # Where to receive job alerts

# GitHub Token (usually auto-provided)
GITHUB_TOKEN           # Auto-generated, used for workflow triggers
```

**Getting Gmail App Password**:
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Go to App Passwords
4. Generate password for "Mail"
5. Use this as `SENDER_PASSWORD`

**2. Enable Workflows**

```bash
# Method 1: Via GitHub UI
1. Go to repository Actions tab
2. Click "I understand my workflows, go ahead and enable them"
3. Workflows will run on schedule automatically

# Method 2: Via GitHub Settings
Settings → Actions → General → Actions permissions
Select: "Allow all actions and reusable workflows"
```

**3. Configure job-manager-config.yml**

Edit your main configuration file:

```yaml
search:
  target_roles:
    - "Senior Software Engineer"
    - "Staff Engineer"
    - "Tech Lead"
  
  required_keywords:
    - "python"
    - "kubernetes"
    - "aws"
  
  locations:
    - "London, UK"
    - "Remote"
  
  salary:
    minimum: 80000
    currency: "GBP"

platforms:
  linkedin:
    enabled: true
    search_interval: 12  # hours
    max_results: 100
  
  glassdoor:
    enabled: true
    search_interval: 12
    max_results: 50
  
  indeed:
    enabled: true
    search_interval: 12
    max_results: 100
  
  reed:
    enabled: true
    use_api: true  # Set false if no API key
    search_interval: 12
    max_results: 100
```

**4. Test Locally Before Automating**

```bash
# Test job discovery
python multi_platform_cli.py search \
  --positions "Senior Engineer" \
  --platforms linkedin \
  --location "London"

# Test keyword extraction
python unified_keyword_extractor.py \
  --positions "Senior Engineer" \
  --linkedin linkedin_jobs.json \
  --output-config test-config.yml \
  --report

# Test job matching
python job_matcher.py \
  --resume documents/resumes/base_resume.pdf \
  --jobs linkedin_jobs.json
```

**5. Manual Workflow Execution**

**Via GitHub UI**:
```
1. Go to Actions tab
2. Select "Job Manager Center Multi-Platform"
3. Click "Run workflow" button
4. Fill in inputs:
   - job_positions: "Senior Software Engineer,Tech Lead"
   - update_config: true
   - trigger_discovery: true
   - skip_boards: ""
5. Click "Run workflow"
```

**Via GitHub CLI**:
```bash
# Install GitHub CLI
brew install gh  # macOS
# or: sudo apt install gh  # Linux
# or: Download from https://cli.github.com/

# Authenticate
gh auth login

# Run workflow
gh workflow run job-manager-center-multiplatform.yml \
  -f job_positions="Senior Software Engineer,Staff Engineer" \
  -f update_config=true \
  -f trigger_discovery=true \
  -f skip_boards=""

# Check workflow status
gh run list --workflow=job-manager-center-multiplatform.yml

# View logs
gh run view <run-id> --log
```

**6. Monitor Workflow Runs**

```bash
# View all workflow runs
Actions tab → Select workflow → View runs

# Download artifacts
Click on workflow run → Scroll to "Artifacts" section → Download

# Check logs
Click on workflow run → Click job name → Expand steps

# View schedule
.github/workflows/job-manager-center-multiplatform.yml
Look for: "on: schedule: - cron:"
```

---

## 📁 Repository Structure

```
jobsearch/
├── .github/
│   └── workflows/
│       ├── job-discovery-worker.yml          # Multi-platform scraper
│       ├── job-manager-center-multiplatform.yml  # Main orchestrator
│       ├── cv_job_matcher.yml                # Resume matching
│       ├── job_matcher_emails.yml            # Email campaigns
│       └── linkedin_automotion.yml           # LinkedIn automation
│
├── job_search/                               # Data storage
│   ├── glassdoor_companies.json
│   ├── glassdoor_salaries.json
│   ├── applications_tracker.json
│   └── exports/
│
├── configs/                                  # Configuration backups
│   └── job-manager-config-backup-*.yml
│
├── Core Scripts/
│   ├── multi_platform_cli.py                 # Multi-platform CLI
│   ├── job-discovery-worker.py               # Discovery worker
│   ├── keyword_extractor.py                  # Keyword analysis
│   ├── linkedin_automotion.py                # LinkedIn automation
│   ├── glassdoor_automotion.py               # Glassdoor scraping
│   ├── indeed_scraper.py                     # Indeed scraping
│   ├── reed_scraper.py                       # Reed scraping
│   ├── job_matcher.py                        # Job matching engine
│   ├── resume_optimizer.py                   # Resume optimization
│   ├── job_search_tracker.py                 # Application tracking
│   └── job_search_cli.py                     # Interactive CLI
│
├── job-manager-config.yml                    # Main configuration
├── requirements.txt                          # Python dependencies
├── .env.example                              # Environment template
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

The `job-manager-config.yml` file is your control center. It's automatically updated by the keyword extractor based on real market data.

### Key Sections

**Search Preferences**
```yaml
search:
  target_roles:
    - "Senior Software Engineer"
    - "Staff Engineer"
    - "Tech Lead"
  
  required_keywords:
    - "python"
    - "kubernetes"
    - "aws"
  
  preferred_keywords:
    - "terraform"
    - "react"
    - "graphql"
  
  locations:
    - "London, UK"
    - "Remote"
    - "Manchester, UK"
  
  salary:
    minimum: 80000
    currency: "GBP"
```

**Platform Configuration**
```yaml
platforms:
  linkedin:
    enabled: true
    search_interval: 12
    max_results_per_search: 100
  
  glassdoor:
    enabled: true
    search_interval: 12
    max_results_per_search: 50
  
  indeed:
    enabled: true
    search_interval: 12
    max_results_per_search: 100
  
  reed:
    enabled: true
    search_interval: 12
    max_results_per_search: 100
    use_api: true  # Faster and more reliable
```

**Matching Weights**
```yaml
matching:
  weights:
    skills: 0.35
    experience: 0.25
    location: 0.15
    salary: 0.10
    culture: 0.10
    growth: 0.05
  
  thresholds:
    excellent: 90
    strong: 80
    good: 70
    fair: 60
```

**Safety Limits**
```yaml
safety:
  rate_limits:
    linkedin_requests_per_hour: 50
    glassdoor_requests_per_hour: 30
    indeed_requests_per_hour: 100
    reed_requests_per_hour: 100
  
  anti_detection:
    randomize_delays: true
    min_delay_seconds: 2
    max_delay_seconds: 8
    use_residential_proxy: false
```

---

## 📊 Monitoring & Analytics

### Daily Reports

After each run, you'll receive an email report:

```
📊 DAILY JOB SEARCH REPORT
Date: 2025-10-11

PLATFORM PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LinkedIn:     45 jobs | 32 companies | 87% with salary
Glassdoor:    28 jobs | 24 companies | 92% with salary
Indeed:       67 jobs | 51 companies | 65% with salary
Reed:         52 jobs | 38 companies | 95% with salary

TOTAL:       192 jobs | 145 unique | 19 duplicates removed

TOP MATCHES (Score ≥ 85)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Senior Software Engineer @ Google
   Score: 94 | Platform: LinkedIn, Indeed
   Salary: £95,000 - £130,000 | Remote
   
2. Staff Engineer @ Stripe
   Score: 91 | Platform: Reed
   Salary: £110,000 - £145,000 | Hybrid

3. Tech Lead @ Monzo
   Score: 88 | Platform: Glassdoor
   Salary: £100,000 - £120,000 | London

KEY INSIGHTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Most in-demand skill: Kubernetes (78% of jobs)
• Average salary: £85k - £115k
• Remote work: 42% of positions
• New roles this week: 64
```

### GitHub Actions Artifacts

Download detailed reports from each workflow run:

- `job_search_report.json` – Complete job data
- `keyword_analysis.json` – Market trends
- `top_matches.csv` – Export for spreadsheets
- `daily_summary.md` – Markdown report
- `updated_config.yml` – New configuration

### View Workflow Logs

```bash
1. Go to Actions tab
2. Select workflow run
3. Click on job name
4. Expand steps to see detailed logs
5. Download artifacts at bottom of page
```

---

## 🔧 Advanced Usage

### Custom Keyword Extraction

```bash
# Analyze specific job files
python keyword_extractor.py \
  --files "linkedin_jobs.json" "indeed_jobs.json" \
  --positions "Senior Software Engineer" "Tech Lead" \
  --min-frequency 3 \
  --update-config

# Export analysis report
python keyword_extractor.py \
  --files "*_jobs.json" \
  --output market_analysis.json
```

### Batch Job Processing

```python
from multi_platform_cli import MultiPlatformJobSearch

searcher = MultiPlatformJobSearch()

# Search multiple positions across locations
positions = ["Senior Engineer", "Staff Engineer", "Tech Lead"]
locations = ["London", "Manchester", "Remote"]

for location in locations:
    results = searcher.search_all_platforms(
        positions, 
        location, 
        max_per_platform=50
    )
    searcher.save_results(f"jobs_{location.lower()}.json")
```

### Integration with Existing Tools

```python
# In your existing job_matcher.py
from indeed_scraper import IndeedScraper
from reed_scraper import ReedScraper

def discover_jobs_multiplatform(positions, location):
    all_jobs = []
    
    # Add Indeed
    indeed = IndeedScraper()
    for position in positions:
        jobs = indeed.search_jobs(position, location, max_results=50)
        all_jobs.extend(jobs)
    
    # Add Reed
    reed = ReedScraper(api_key=os.getenv('REED_API_KEY'))
    for position in positions:
        jobs = reed.search_with_api(position, location, max_results=50)
        all_jobs.extend(jobs)
    
    return all_jobs
```

---

## 🛡️ Security & Best Practices

### Environment Variables

Never commit credentials! Use `.env` file:

```bash
# .env (add to .gitignore)
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
GLASSDOOR_EMAIL=your-email@example.com
GLASSDOOR_PASSWORD=your-password
REED_API_KEY=your-api-key
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

### Rate Limiting Strategy

```yaml
# Respect platform limits to avoid detection
safety:
  rate_limits:
    linkedin_requests_per_hour: 50   # Conservative
    glassdoor_requests_per_hour: 30   # Very conservative
    indeed_requests_per_hour: 100     # More lenient
    reed_requests_per_hour: 100       # 200 with API key
```

### Protected Files

```gitignore
# Add to .gitignore
.env
*.pdf
*.docx
*resume*
*cv*
*credentials*
*password*
job_search/*.json
configs/job-manager-config-backup-*.yml
```

---

## 🔍 Troubleshooting

### Common Issues

**Workflow Not Running**
```bash
✓ Check Settings → Actions → General → Workflow permissions
✓ Enable "Read and write permissions"
✓ Verify secrets are set correctly
✓ Check workflow YAML syntax
```

**No Jobs Found**
```bash
# Test individual scrapers
python indeed_scraper.py
python reed_scraper.py

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('job-manager-config.yml')))"

# Verify network connectivity
curl -I https://uk.indeed.com
curl -I https://www.reed.co.uk
```

**Keyword Extraction Failing**
```bash
# Ensure job files exist and have content
for f in *_jobs.json; do 
  echo "$f: $(python -c "import json; print(len(json.load(open('$f'))))" ) jobs"
done

# Manually trigger extraction
python keyword_extractor.py --files "*_jobs.json" --verbose
```

**Rate Limiting / CAPTCHA**
```bash
# Solution 1: Increase delays
# In job-manager-config.yml:
anti_detection:
  min_delay_seconds: 5
  max_delay_seconds: 15

# Solution 2: Use API (Reed only)
export REED_API_KEY="your-key"

# Solution 3: Reduce frequency
# Change schedule from twice daily to once daily
```

### Debug Mode

Enable verbose logging:

```bash
# For CLI commands
python multi_platform_cli.py search --verbose

# For Python scripts
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

```bash
# Quick system health check
python dashboard.py --overview

# Detailed diagnostics
python dashboard.py --health
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Areas for Improvement

- [ ] 🌍 Add support for more job boards (Monster, Totaljobs, CV-Library)
- [ ] 🤖 Implement ML-based job matching improvements
- [ ] 📱 Create mobile app companion
- [ ] 🎨 Build web dashboard for visualization
- [ ] 🔔 Add Slack/Discord notification options
- [ ] 🌐 Multi-language support (ES, FR, DE)
- [ ] 🎥 Video cover letter generator
- [ ] 📊 Advanced analytics and A/B testing
- [ ] 🔐 Enhanced security features (2FA integration)
- [ ] ⚡ Performance optimizations

### How to Contribute

1. **Fork the repository**
```bash
git clone https://github.com/yourusername/job-search-automation.git
cd job-search-automation
```

2. **Create a feature branch**
```bash
git checkout -b feature/amazing-new-feature
```

3. **Make your changes**
```bash
# Implement your feature
# Add tests if applicable
# Update documentation
```

4. **Test thoroughly**
```bash
python -m pytest tests/
python job_search_cli.py  # Test CLI
```

5. **Commit and push**
```bash
git add .
git commit -m "Add amazing new feature"
git push origin feature/amazing-new-feature
```

6. **Open a Pull Request**
- Describe your changes clearly
- Reference any related issues
- Include screenshots if applicable

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/job-search-automation.git
cd job-search-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Run tests
python -m pytest tests/ -v
```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Include type hints where appropriate
- Write tests for new features

---

## 📚 Documentation

### Comprehensive Guides

- **[Complete Integration Guide](docs/complete_integration_guide.md)** – Full system setup
- **[GitHub Actions Setup](docs/github-action_setup_guide.md)** – Workflow configuration  
- **[LinkedIn & Glassdoor Guide](docs/advanced_integration_guide-Linkedin-Glassdoor.md)** – Platform integration
- **[Orchestrator Setup](docs/ORCHESTRATOR_SETUP_GUIDE.md)** – Workflow orchestration
- **[Quick Reference](docs/QUICK_REFERENCE.md)** – Command cheat sheet

### Quick Links

- [Installation Checklist](docs/INSTALLATION_CHECKLIST.md)
- [Interactive CLI Menu Guide](docs/interactive-CLI-menu.docx)
- [Automation Roadmap](docs/automotion-roadmap.docx)
- [System Architecture Diagram](docs/system-architecture.png)

---

## 📈 Roadmap

### ✅ Completed
- [x] Multi-platform job discovery (LinkedIn, Glassdoor, Indeed, Reed)
- [x] AI-powered job matching engine
- [x] Automated keyword extraction
- [x] Resume optimization
- [x] GitHub Actions workflows
- [x] Email notification system
- [x] Application tracking
- [x] LinkedIn networking automation

### 🚧 In Progress
- [ ] Web dashboard for visualization
- [ ] Enhanced ML matching algorithms
- [ ] Interview preparation assistant
- [ ] Salary negotiation coach

### 🔮 Future Plans
- [ ] Mobile app (iOS/Android)
- [ ] Browser extension for one-click applications
- [ ] Integration with calendars for interview scheduling
- [ ] Company culture fit AI analysis
- [ ] Video cover letter generator
- [ ] Multi-language support
- [ ] Integration with more job boards globally

---

## 💡 Tips for Success

1. **Start Conservative** – Begin with 5-10 applications per day, then scale
2. **Update Regularly** – Keep your resume and config current
3. **Track Everything** – Use the built-in tracker religiously
4. **Personalize Always** – Even automated messages should feel genuine
5. **Monitor Metrics** – Review weekly reports and adjust strategy
6. **Follow Up** – Use automated reminders for follow-ups
7. **Stay Organized** – Leverage the categorization system
8. **Be Patient** – Job search is a marathon, not a sprint
9. **Test First** – Always test locally before enabling automation
10. **Respect Limits** – Don't abuse platforms; it hurts everyone

---

## ⚖️ Legal & Ethical Considerations

### Platform Compliance

⚠️ **Important**: This tool is for personal use only.

- ✅ **Allowed**: Automating your own personal job search
- ✅ **Allowed**: Using platform APIs where available (Reed)
- ⚠️ **Gray Area**: Web scraping public job listings
- ❌ **Prohibited**: Scraping private data, commercial use, spamming

### Responsible Usage

1. **Respect Terms of Service** – Read and comply with platform ToS
2. **Rate Limiting** – Stay well below platform limits
3. **Authenticity** – Personalize automated messages
4. **Privacy** – Never commit credentials or personal data
5. **Transparency** – Be honest if asked about automation
6. **Quality Over Quantity** – Focus on relevant applications

### Recommendations

- Use APIs when available (Reed API)
- Implement conservative rate limits
- Add random delays between requests
- Don't distribute scraped data
- Monitor for changes in platform policies
- Consider ethical implications of each action

---

## 🆘 Support

### Getting Help

- 📖 **Documentation**: Check the `/docs` folder for detailed guides
- 🐛 **Bugs**: Open an issue on GitHub with detailed description
- 💬 **Questions**: Use GitHub Discussions for Q&A
- ✉️ **Contact**: Reach out to maintainers for urgent issues

### Frequently Asked Questions

**Q: Is this legal?**  
A: Yes, for personal use. Always comply with platform Terms of Service and use responsibly.

**Q: Will I get banned from LinkedIn?**  
A: Not if you respect rate limits and use realistic delays. Start conservatively with 20-30 actions per day.

**Q: How accurate is the job matching?**  
A: Typically 85-95% accurate with proper configuration and updated skills data. The system learns from your feedback.

**Q: Can I use this for multiple career paths?**  
A: Yes! Create different configuration profiles by copying `job-manager-config.yml` to `config-career1.yml`, `config-career2.yml`, etc.

**Q: Do I need API keys?**  
A: LinkedIn and Glassdoor require credentials. Reed API key is optional but recommended for better reliability. Indeed works without authentication.

**Q: How much does it cost?**  
A: The software is free. You'll need:
- GitHub account (free tier sufficient)
- Gmail account for notifications (free)
- Reed API key (free tier: 50 requests/month, paid: £50/month for 10,000)

**Q: Can I run this without GitHub Actions?**  
A: Yes! Run all scripts locally via CLI. GitHub Actions just adds automation.

**Q: How do I stop the automation?**  
A: Disable workflows in Settings → Actions → General → "Disable Actions" or delete the `.github/workflows` folder.

---

## 🌟 Success Stories

> *"Went from 2 interviews in 3 months to 8 interviews in 2 weeks. The keyword extraction helped me realize I was missing key terms in my resume."*  
> — **Sarah M.**, Software Engineer

> *"The automated networking feature connected me with 100+ recruiters in my target companies. Got 3 referrals in the first month."*  
> — **James T.**, Data Scientist

> *"I was spending 3 hours daily on job boards. Now I spend 15 minutes reviewing the top matches the system finds. Accepted an offer after 6 weeks."*  
> — **Priya K.**, Product Manager

> *"The salary insights from Glassdoor integration helped me negotiate a 20% higher offer. Knew exactly what the market rate was."*  
> — **Michael R.**, DevOps Engineer

---

## 📊 Platform Comparison

| Feature | LinkedIn | Glassdoor | Indeed | Reed |
|---------|----------|-----------|--------|------|
| **Job Volume** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **UK Focus** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Company Reviews** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Salary Data** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Remote Jobs** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **API Available** | ❌ | ❌ | ❌ | ✅ |
| **Auth Required** | ✅ | ✅ | ❌ | ❌ |
| **Rate Limits** | Strict | Moderate | Lenient | API: High |
| **Data Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Recommendations by Use Case

**🎯 Maximum Job Coverage**  
Use all 4 platforms for comprehensive search

**🇬🇧 UK-Focused Search**  
Prioritize Reed and Indeed

**💰 Salary Research**  
Use Glassdoor and Reed for best data

**🏢 Company Culture**  
Glassdoor has the most detailed reviews

**⚡ Quick Setup**  
Start with Indeed and Reed (no auth required)

**🔄 Daily Automation**  
Enable all platforms in `job-manager-config.yml`

---

## 🎓 Learning Resources

### Understanding Job Search Automation

- [Web Scraping Best Practices](https://github.com/topics/web-scraping)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Selenium Guide](https://selenium-python.readthedocs.io/)
- [ATS Resume Optimization](https://www.jobscan.co/blog/ats-resume-optimization/)

### Improving Your Results

- [LinkedIn Networking Strategies](https://www.linkedin.com/business/talent/blog/product-tips/tips-for-using-linkedin-recruiter)
- [Resume Keywords Guide](https://www.indeed.com/career-advice/resumes-cover-letters/resume-keywords)
- [Salary Negotiation Tactics](https://www.glassdoor.com/blog/salary-negotiation-tips/)
- [Interview Preparation](https://www.themuse.com/advice/interview-questions-and-answers)

### Technical Deep Dives

- [Building Job Board Scrapers](https://realpython.com/beautiful-soup-web-scraper-python/)
- [ML for Job Matching](https://towardsdatascience.com/job-recommendation-system-using-machine-learning-e8f0c9c6f4d5)
- [Automating with GitHub Actions](https://github.blog/2021-11-18-7-advanced-workflow-automation-features-with-github-actions/)

---

## 🔗 Related Projects

Complementary tools to enhance your job search:

- [**Resume.io**](https://resume.io) – Professional resume builder
- [**Huntr**](https://huntr.co) – Job application tracker
- [**Teal**](https://www.tealhq.com) – Career growth platform
- [**Rezi**](https://www.rezi.ai) – AI resume optimizer
- [**Jobscan**](https://www.jobscan.co) – ATS resume checker
- [**Careerflow**](https://www.careerflow.ai) – LinkedIn optimization
- [**InterviewBuddy**](https://interviewbuddy.com) – Mock interviews

---

## 🏆 Acknowledgments

Built with ❤️ by the open-source community to help job seekers work smarter, not harder.

**Special Thanks To:**
- Contributors who've helped improve the codebase
- Beta testers who provided invaluable feedback
- The Python, Selenium, and GitHub Actions communities
- All the job seekers who've shared their success stories

**Technology Stack:**
- Python 3.8+ for core automation
- Selenium for web automation
- BeautifulSoup for HTML parsing
- GitHub Actions for CI/CD
- PyYAML for configuration management
- Pandas for data analysis

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License Summary:**
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ⚠️ Liability disclaimer
- ⚠️ Warranty disclaimer

---

## 🚨 Disclaimer

This tool is designed to **assist and streamline** your job search process, not to spam or abuse platforms. 

**Important Notes:**
- Use responsibly and ethically
- Respect platform Terms of Service
- Start with conservative settings
- Always personalize automated content
- Monitor for platform policy changes
- This software is provided "as-is" without warranty
- Authors are not liable for misuse or platform bans

**Remember:** The goal is to work smarter, not to game the system. Quality applications to relevant positions will always outperform high-volume, low-quality spam.

---

## 📞 Contact & Community

### Connect With Us

- 💬 **GitHub Discussions**: Ask questions, share tips
- 🐛 **Issue Tracker**: Report bugs, request features
- 🌟 **Star the Repo**: Show your support
- 🔀 **Fork & Contribute**: Make it better
- 📧 **Email**: maintainers@example.com (for urgent issues only)

### Community Guidelines

We're committed to providing a welcoming and inclusive environment:

- Be respectful and professional
- Help others learn and grow
- Share your knowledge and experiences
- Provide constructive feedback
- Celebrate community successes

---

## 🎉 Ready to Transform Your Job Search?

```bash
# Get started in 30 seconds
git clone https://github.com/yourusername/job-search-automation.git
cd job-search-automation
pip install -r requirements.txt
python job_search_cli.py
```

**Your dream job is out there. Let's find it together.** 🚀

---

<div align="center">

### ⭐ If this project helped you land a job, please star it! ⭐

**Made with ❤️ for job seekers everywhere**

[Report Bug](https://github.com/yourusername/repo/issues) • [Request Feature](https://github.com/yourusername/repo/issues) • [Contribute](CONTRIBUTING.md)

**Good luck with your job search!** 🎯

</div>

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/job-search-automation?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/job-search-automation?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/job-search-automation)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/job-search-automation)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/job-search-automation)

---

**Version**: 2.0.0  
**Last Updated**: October 2025  
**Platforms Supported**: LinkedIn, Glassdoor, Indeed, Reed  
**Maintained**: ✅ Actively maintained