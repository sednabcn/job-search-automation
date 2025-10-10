# 🔍 Job Search Automation Suite

Comprehensive job search automation system with multi-platform integration, AI-powered matching, resume optimization, and automated tracking across LinkedIn, Glassdoor, and professional job centers.

## 📋 Features

### 🎯 Core Functionality
- ✅ **Multi-Platform Job Search** - LinkedIn, Glassdoor, and job board automation
- 🤖 **AI-Powered Matching** - Intelligent job-resume compatibility analysis
- 📄 **Resume Optimization** - ATS-friendly formatting and keyword optimization
- 💼 **Application Tracking** - Complete application lifecycle management
- 🔗 **LinkedIn Networking** - Automated connection requests and engagement
- 💰 **Salary Analysis** - Comprehensive compensation insights
- ⭐ **Company Research** - Employee reviews and culture reports
- 📊 **Interview Preparation** - Question analysis and prep guides

### 🚀 Enhanced Features
- 📤 **Export Capabilities** - CSV, Markdown, and comparison reports
- 🔎 **Advanced Search** - Filter by rating, industry, location, salary
- 🏆 **Rankings** - Find best companies and highest paying roles
- 🤖 **GitHub Actions** - Automated daily searches and monitoring
- 📧 **Email Campaigns** - Tailored application submissions
- 📈 **Weekly Summaries** - Automated progress reports
- 🔄 **Referral Automation** - Streamlined referral request workflows

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- GitHub account (for Actions automation)
- LinkedIn account
- Glassdoor account (optional)
- Gmail account (for email notifications)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sednabcn/jobsearch.git
cd jobsearch
```

2. **Run the quick setup script**
```bash
chmod +x quick_setup_script.sh
./quick_setup_script.sh
```

3. **Or install manually**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

Create a `.env` file with your credentials:

```env
# LinkedIn Credentials
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password

# Glassdoor Credentials
GLASSDOOR_EMAIL=your.email@example.com
GLASSDOOR_PASSWORD=your_password

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=your_app_password

# Job Search Preferences
LOCATION=London, UK
JOB_TITLES=Data Scientist,Machine Learning Engineer
EXPERIENCE_LEVEL=Mid-Senior level
```

## 💻 Usage

### Interactive CLI

Start the interactive menu for guided job search:

```bash
python job_search_cli.py
```

### LinkedIn Automation

```bash
# Automated job search
python linkedin_automotion.py --keywords "Python Developer" --location "London"

# Advanced networking
python linkedin_advanced_networking.py --target-companies "Google,Amazon,Meta" --connection-limit 50
```

### Glassdoor Research

```bash
# Add company to research
python glassdoor_automotion.py --company "Google" --priority high --role "Software Engineer"

# Get salary insights
python glassdoor_automotion.py --salary "Google" --role "Engineer"

# Generate full report
python enhanced_glassdoor_automotion.py --report "Google" -o google_report.md
```

### Job Matching & Optimization

```bash
# Match resume to job description
python job_matcher.py --resume cv.pdf --job-url "https://linkedin.com/jobs/view/123456"

# Optimize resume for specific job
python resume_optimizer.py --input cv.docx --job-description job.txt --output optimized_cv.docx

# Combined resume and cover letter optimization
python Resume-Cover-Letter_Optimizer.py --job-url "https://example.com/job"
```

### Application Tracking

```bash
# Track applications
python job_search_tracker.py --add "Company Name" "Position" "Applied"

# View statistics
python job_search_tracker.py --stats

# Get daily tasks
python job_search_tracker.py --tasks
```

### Job Board Monitoring

```bash
# Continuous monitoring (check every hour)
python job_board_monitor.py --interval 3600

# Multi-platform search
python professionaal-jobcenter.py --keywords "Data Analyst" --location "UK"
```

### Referral Automation

```bash
# Automated referral requests
python referral_automotion.py --company "Google" --role "Software Engineer"
```

## 🤖 GitHub Actions Setup

### 1. Setup Repository Structure

```
jobsearch/
├── .github/
│   ├── workflows/
│   │   ├── job_search_workflow.yml
│   │   ├── cv_job_matcher.yml
│   │   ├── job_matcher_emails.yml
│   │   ├── linkedin_automotion.yml
│   │   └── glassdor_automotion.yml
│   └── scripts/                    # GitHub Actions helper scripts
├── job_search/
│   ├── glassdoor_companies.json
│   ├── glassdoor_salaries.json
│   ├── glassdoor_interviews.json
│   ├── applications_tracker.json
│   └── exports/
├── Core Automation Scripts (root directory)
│   ├── linkedin_automotion.py
│   ├── glassdoor_automotion.py
│   ├── enhanced_glassdoor_automotion.py
│   ├── job_matcher.py
│   ├── resume_optimizer.py
│   └── ... (all other .py files)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### 2. Enable GitHub Actions

1. Go to your repository settings
2. Navigate to **Actions** → **General**
3. Under **Workflow permissions**, select "Read and write permissions"
4. Check "Allow GitHub Actions to create and approve pull requests"

### 3. Add Repository Secrets

Go to Settings → Secrets and variables → Actions and add:

```
LINKEDIN_EMAIL
LINKEDIN_PASSWORD
GLASSDOOR_EMAIL
GLASSDOOR_PASSWORD
SMTP_HOST
SMTP_PORT
SENDER_EMAIL
SENDER_PASSWORD
```

### 4. Automated Workflows

#### Daily Job Search (9 AM UTC)
- ✅ Searches LinkedIn for new positions
- ✅ Monitors Glassdoor opportunities
- ✅ Matches jobs with your resume
- ✅ Sends email alerts for top matches

#### CV Job Matcher (On demand)
- ✅ Analyzes job descriptions
- ✅ Scores job-resume compatibility
- ✅ Generates optimization suggestions
- ✅ Creates tailored applications

#### Email Campaigns (Scheduled)
- ✅ Sends personalized applications
- ✅ Tracks email delivery
- ✅ Manages follow-ups
- ✅ Handles responses

#### Weekly Summary (Mondays)
- ✅ Analyzes past week's activity
- ✅ Highlights top opportunities
- ✅ Creates progress report
- ✅ Identifies action items

## 📤 Export Formats

### CSV Exports
```python
# All companies
enhanced.export_companies_csv()

# Salaries for specific company
enhanced.export_salaries_csv("Google")

# All interviews
enhanced.export_interviews_csv()

# Company comparison
enhanced.export_comparison_csv(["Google", "Meta", "Amazon"])

# Application tracking
tracker.export_to_csv("applications.csv")
```

### Markdown Reports
```python
# Full research report
enhanced.export_full_report_markdown("Google")

# Job matching report
matcher.export_match_report("match_results.md")

# Weekly summary
tracker.generate_weekly_summary("weekly_report.md")
```

## 🔎 Advanced Search & Filtering

### Search Companies
```python
results = enhanced.search_companies(
    name="Tech",
    industry="Software",
    min_rating=4.0,
    max_rating=5.0,
    location="San Francisco"
)
```

### Search Jobs by Criteria
```python
jobs = matcher.search_jobs(
    keywords=["Python", "Machine Learning"],
    min_salary=150000,
    experience_level="Senior",
    remote=True,
    posted_within_days=7
)
```

### Find Best Companies
```python
# Best work-life balance
best = enhanced.find_best_companies(
    criteria="work_life_balance",
    min_reviews=10,
    limit=10
)

# Highest paying companies for role
top_paying = enhanced.find_high_paying_roles(
    role_keyword="Machine Learning Engineer",
    min_compensation=200000,
    limit=10
)
```

## 📊 Data Structure

### Job Applications
```json
{
  "id": "APP-20251010120000",
  "company_name": "OpenAI",
  "position": "ML Engineer",
  "status": "Applied",
  "applied_date": "2025-10-10",
  "match_score": 92,
  "salary_range": "200k-350k",
  "location": "San Francisco, CA"
}
```

### Company Research
```json
{
  "id": "COMP-20251010120000",
  "company_name": "OpenAI",
  "overall_rating": 4.5,
  "ceo_approval": 95,
  "industry": "AI",
  "size": "500-1000",
  "headquarters": "San Francisco, CA",
  "work_life_balance": 4.2
}
```

### Salary Data
```json
{
  "company_name": "OpenAI",
  "role": "ML Engineer",
  "base_salary_avg": 215000,
  "total_comp_avg": 325000,
  "location": "San Francisco, CA",
  "experience_level": "Mid-Senior",
  "equity_avg": 60000
}
```

### Job Matches
```json
{
  "job_id": "JOB-123456",
  "match_score": 92,
  "skills_match": 88,
  "experience_match": 95,
  "location_match": 100,
  "salary_match": 90,
  "recommendations": ["Add AWS certification", "Emphasize ML experience"]
}
```

## 🎯 Job Matcher Engine

The AI-powered matcher analyzes:

- ✅ **Skills Alignment** - Required vs. nice-to-have skills (35% weight)
- ✅ **Experience Level** - Years of experience matching (25% weight)
- ✅ **Location Compatibility** - Remote, hybrid, or on-site (15% weight)
- ✅ **Salary Range Fit** - Compensation expectations (10% weight)
- ✅ **Company Culture** - Values and work style alignment (10% weight)
- ✅ **Career Growth** - Progression potential (5% weight)

**Scoring System:**
- 90-100: Excellent match - Apply immediately
- 80-89: Strong match - Highly recommended
- 70-79: Good match - Consider applying
- 60-69: Fair match - Review carefully
- Below 60: Poor match - May not be suitable

## 📝 Resume Optimizer

### Optimization Features
- 📝 **Keyword Density Analysis** - Ensure ATS compatibility
- 📝 **Action Verb Enhancement** - Strengthen impact statements
- 📝 **Quantifiable Achievements** - Add metrics and results
- 📝 **Industry Terminology** - Align with job description language
- 📝 **Section Prioritization** - Highlight most relevant experience
- 📝 **ATS-Friendly Formatting** - Remove problematic elements

### Optimization Process
```python
# 1. Analyze job description
job_analysis = optimizer.analyze_job_description(job_url)

# 2. Extract key requirements
requirements = optimizer.extract_requirements(job_analysis)

# 3. Optimize resume
optimized_resume = optimizer.optimize_resume(
    original_resume="cv.docx",
    requirements=requirements,
    emphasis=["technical_skills", "leadership"]
)

# 4. Generate cover letter
cover_letter = optimizer.generate_cover_letter(
    resume=optimized_resume,
    job_analysis=job_analysis,
    tone="professional"
)
```

## 🔗 LinkedIn Automation Features

### Networking Capabilities
- 🔗 **Advanced Search** - Multi-filter job and people search
- 🔗 **Connection Automation** - Smart connection requests with personalization
- 🔗 **Profile Viewing** - Strategic profile engagement
- 🔗 **Job Application** - Automated application submission
- 🔗 **InMail Campaigns** - Targeted messaging to recruiters
- 🔗 **Network Expansion** - Second and third-degree connections
- 🔗 **Engagement Tracking** - Monitor interactions and responses

### Best Practices
```python
networking = LinkedInNetworking()

# Smart connection requests (personalized)
networking.connect_with_targets(
    target_companies=["Google", "Meta", "Amazon"],
    roles=["Recruiter", "Hiring Manager", "Team Lead"],
    max_daily=50,  # Stay under LinkedIn limits
    personalize=True
)

# Automated follow-ups
networking.follow_up_connections(days_since_connect=7)
```

## 🏢 Glassdoor Integration

### Research Features
- 🏢 **Company Profiles** - Comprehensive company information
- 🏢 **Salary Insights** - Role-specific compensation data
- 🏢 **Interview Reviews** - Real interview experiences
- 🏢 **Culture Analysis** - Employee review aggregation
- 🏢 **Benefits Comparison** - Perks and benefits analysis
- 🏢 **CEO Ratings** - Leadership approval scores

## 📧 Email Campaign System

### Features
- 📧 **Template Management** - Customizable email templates
- 📧 **Personalization** - Dynamic content replacement
- 📧 **Batch Sending** - Rate-limited bulk sending
- 📧 **Tracking** - Open rates and responses
- 📧 **Follow-up Automation** - Scheduled follow-up emails
- 📧 **Unsubscribe Handling** - Automatic opt-out management

## 🔔 Notifications

### GitHub Issues
- 🔴 **High Priority Jobs** - Immediate alerts for excellent matches (>90 score)
- 📊 **Weekly Summary** - Progress reports every Monday
- ⚠️ **Application Deadlines** - Alerts for closing applications
- 📈 **Match Notifications** - Daily digest of new matches

### Email Alerts
- 📧 **Top Matches** - Instant notifications for jobs >85 match score
- 📧 **Interview Invitations** - Auto-forward interview requests
- 📧 **Application Status** - Updates on application progress

### Artifacts
- 📦 **Daily Reports** - Job search activity (30-day retention)
- 📦 **Weekly Summaries** - Progress and insights (90-day retention)
- 📦 **Export Files** - CSV and Markdown exports
- 📦 **Match Reports** - Detailed compatibility analyses

## 🛠️ Customization

### Modify Search Parameters

Edit workflow files or configuration:

```python
# In your config file or workflow
SEARCH_CONFIG = {
    "keywords": ["Data Scientist", "ML Engineer"],
    "locations": ["London, UK", "Remote"],
    "experience_levels": ["Mid-Senior level", "Director"],
    "min_salary": 80000,
    "job_types": ["Full-time", "Contract"],
    "remote_preference": "Remote or Hybrid",
    "posted_within_days": 7
}
```

### Custom Matching Weights

```python
# Adjust importance of different criteria
MATCH_WEIGHTS = {
    "skills": 0.40,        # 40% weight
    "experience": 0.25,    # 25% weight
    "location": 0.15,      # 15% weight
    "salary": 0.10,        # 10% weight
    "culture": 0.05,       # 5% weight
    "growth": 0.05         # 5% weight
}
```

### Schedule Customization

Edit `.github/workflows/*.yml`:

```yaml
on:
  schedule:
    - cron: '0 9 * * *'    # Daily at 9 AM UTC
    - cron: '0 9 * * 1'    # Weekly on Monday
    - cron: '0 */6 * * *'  # Every 6 hours
```

## 📈 Monitoring & Analytics

### View Workflow Results
1. Go to **Actions** tab in GitHub
2. Select workflow run
3. Download artifacts (reports, exports, summaries)
4. Review logs for detailed execution info

### Track Success Metrics
```python
# Generate analytics report
tracker.generate_analytics({
    "applications_sent": 45,
    "responses_received": 12,
    "interviews_scheduled": 5,
    "offers_received": 2,
    "response_rate": "26.7%",
    "interview_rate": "11.1%",
    "offer_rate": "4.4%"
})
```

### Monitor Data Quality
- Review data completeness reports
- Validate job matching accuracy
- Check application status updates
- Audit email delivery rates

## 🔒 Security

### Best Practices
- ✅ **No Hardcoded Credentials** - Use environment variables
- ✅ **GitHub Secrets** - Store sensitive data securely
- ✅ **Private Repository** - Keep job search data private
- ✅ **`.gitignore`** - Exclude personal documents
- ✅ **Regular Audits** - Review access logs
- ✅ **2FA Enabled** - Protect LinkedIn and GitHub accounts

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
```

## ⚠️ Legal & Ethical Considerations

### Platform Compliance
- ⚖️ **Terms of Service** - Ensure compliance with platform ToS
- ⚖️ **Rate Limiting** - Respect API limits and implement delays
- ⚖️ **Privacy** - Never commit credentials or personal data
- ⚖️ **Authenticity** - Use automation to enhance, not replace, genuine engagement

### Responsible Usage
1. **Start Slow** - Test with small batches
2. **Human Review** - Always review before sending
3. **Personalization** - Customize each application
4. **Respect Limits** - Don't spam platforms
5. **Be Genuine** - Maintain authentic interactions

## 🐛 Troubleshooting

### GitHub Actions Not Running
- ✅ Check workflow permissions in repository settings
- ✅ Verify YAML syntax in workflow files
- ✅ Review Actions tab for error messages
- ✅ Ensure secrets are properly configured

### LinkedIn Automation Issues
- Reduce request frequency
- Add random delays (5-15 seconds)
- Use residential proxies if blocked
- Enable 2FA and use session tokens
- Check for CAPTCHA requirements

### Job Matching Inaccuracy
- Update skills database in configuration
- Refine matching algorithm weights
- Improve resume parsing accuracy
- Add more training data examples

### Email Delivery Failures
- Check SMTP settings in `.env`
- Enable "App passwords" for Gmail
- Verify recipient email addresses
- Check spam folder
- Review email rate limits

## 📚 Documentation

### Comprehensive Guides
- **[Complete Integration Guide](complete_integration_guide.md)** - Full system setup
- **[GitHub Actions Setup](github-action_setup_guide.md)** - Workflow configuration
- **[LinkedIn & Glassdoor Guide](advanced_integration_guide-Linkedin-Glassdoor.md)** - Platform integration
- **[Job Matcher Documentation](job_matcher.md)** - Algorithm details
- **[Main Guide](main-guide.docx)** - Master reference document

### Quick References
- [Interactive CLI Menu](interactive-CLI-menu.docx) - Command reference
- [Automation Roadmap](automotion-roadmap.docx) - Future features
- [Setup Script Guide](quick_setup_script.sh) - Installation helper

## 📈 Roadmap

### Upcoming Features
- [ ] AI-powered interview preparation assistant
- [ ] Salary negotiation coach with market data
- [ ] Multi-language support (ES, FR, DE)
- [ ] Mobile app companion
- [ ] Interview scheduling automation
- [ ] Company culture fit AI analysis
- [ ] Recruiter outreach automation
- [ ] Portfolio website integration
- [ ] Video cover letter generator
- [ ] Integration with Indeed, Monster, ZipRecruiter

### In Progress
- [x] LinkedIn automation
- [x] Glassdoor integration
- [x] Job matching engine
- [x] Resume optimizer
- [x] GitHub Actions workflows
- [x] Email campaign system

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/jobsearch.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Run tests
python -m pytest tests/
```

## 📄 License

This project is for educational and personal use. Ensure compliance with platform Terms of Service before deploying.

## 💡 Tips for Success

1. **Update Regularly** - Keep your resume and preferences current
2. **Track Everything** - Log all applications and interactions
3. **Set Realistic Goals** - Start with 5-10 applications per day
4. **Follow Up** - Automated reminders help stay on top of responses
5. **Personalize Always** - Even automated messages should feel personal
6. **Monitor Metrics** - Track what works and adjust strategy
7. **Stay Organized** - Use the tracking system religiously
8. **Be Patient** - Job search is a marathon, not a sprint

## 🆘 Support

### Getting Help
- 📖 Check the documentation in `/docs` folder
- 🐛 Open an issue for bugs
- 💬 Discussions tab for questions
- 📧 Contact maintainers for urgent issues

### Common Questions

**Q: Is this legal?**  
A: Yes, for personal use. Always comply with platform ToS and use responsibly.

**Q: Will I get banned from LinkedIn?**  
A: Not if you respect rate limits and use realistic delays. Start conservatively.

**Q: How accurate is the job matching?**  
A: Typically 85-95% accurate with proper configuration and updated skills data.

**Q: Can I use this for multiple job searches?**  
A: Yes! Create different configuration profiles for different career paths.

## ⭐ Acknowledgments

Built to help job seekers work smarter, not harder. Special thanks to the open-source community and all contributors.

---

**Note**: This tool is designed to assist and streamline your job search process, not to spam or abuse platforms. Always use responsibly and ethically. Good luck with your job search! 🎯