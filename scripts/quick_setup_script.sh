#!/bin/bash

# ============================================
# Job Search Automation - Quick Setup Script
# ============================================
# This script automates the initial setup process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emoji support
CHECKMARK="✓"
CROSS="✗"
ARROW="→"
ROCKET="🚀"
WRENCH="🔧"
LOCK="🔒"
FOLDER="📁"

echo -e "${BLUE}${ROCKET} Job Search Automation - Quick Setup${NC}"
echo "=========================================="
echo ""

# ============================================
# Check Prerequisites
# ============================================
echo -e "${BLUE}${WRENCH} Checking prerequisites...${NC}"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}${CHECKMARK} Python 3 found: ${PYTHON_VERSION}${NC}"
else
    echo -e "${RED}${CROSS} Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}${CHECKMARK} pip3 found${NC}"
else
    echo -e "${RED}${CROSS} pip3 not found. Installing...${NC}"
    python3 -m ensurepip --upgrade
fi

# Check git
if command -v git &> /dev/null; then
    echo -e "${GREEN}${CHECKMARK} Git found${NC}"
else
    echo -e "${YELLOW}${CROSS} Git not found. Some features may not work.${NC}"
fi

echo ""

# ============================================
# Create Directory Structure
# ============================================
echo -e "${BLUE}${FOLDER} Creating directory structure...${NC}"

mkdir -p job_search
mkdir -p job_search/exports
mkdir -p logs
mkdir -p downloads
mkdir -p screenshots
mkdir -p documents
mkdir -p templates
mkdir -p .github/workflows
mkdir -p .github/scripts

echo -e "${GREEN}${CHECKMARK} Directories created${NC}"
echo ""

# ============================================
# Setup Virtual Environment
# ============================================
echo -e "${BLUE}${WRENCH} Setting up virtual environment...${NC}"

read -p "Do you want to create a virtual environment? (recommended) [Y/n]: " CREATE_VENV
CREATE_VENV=${CREATE_VENV:-Y}

if [[ $CREATE_VENV =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}${CHECKMARK} Virtual environment created${NC}"
    else
        echo -e "${YELLOW}${CHECKMARK} Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    echo -e "${GREEN}${CHECKMARK} Virtual environment activated${NC}"
else
    echo -e "${YELLOW}${ARROW} Skipping virtual environment creation${NC}"
fi

echo ""

# ============================================
# Install Dependencies
# ============================================
echo -e "${BLUE}${WRENCH} Installing Python dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    echo -e "${GREEN}${CHECKMARK} Dependencies installed successfully${NC}"
else
    echo -e "${YELLOW}${CROSS} requirements.txt not found. Creating basic requirements...${NC}"
    
    cat > requirements.txt << 'EOF'
# Core dependencies
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
pandas>=2.1.0
python-dotenv>=1.0.0

# Browser automation
webdriver-manager>=4.0.0
playwright>=1.40.0

# Data processing
openpyxl>=3.1.0
python-docx>=1.1.0
PyPDF2>=3.0.0

# Email
email-validator>=2.1.0

# Optional: AI features
# openai>=1.3.0
# anthropic>=0.7.0
EOF
    
    pip3 install -r requirements.txt
    echo -e "${GREEN}${CHECKMARK} Basic dependencies installed${NC}"
fi

echo ""

# ============================================
# Setup Environment File
# ============================================
echo -e "${BLUE}${LOCK} Setting up environment configuration...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}${CHECKMARK} Created .env from .env.example${NC}"
        echo -e "${YELLOW}${ARROW} Please edit .env file with your credentials${NC}"
    else
        echo -e "${YELLOW}${CROSS} .env.example not found. Creating basic .env file...${NC}"
        
        cat > .env << 'EOF'
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
MIN_SALARY=80000
MAX_SALARY=200000

# Automation Settings
MAX_APPLICATIONS_PER_DAY=20
ENABLE_AUTO_APPLY=false
TEST_MODE=false
EOF
        
        echo -e "${GREEN}${CHECKMARK} Basic .env file created${NC}"
        echo -e "${YELLOW}${ARROW} Please edit .env file with your credentials${NC}"
    fi
else
    echo -e "${YELLOW}${CHECKMARK} .env file already exists${NC}"
fi

echo ""

# ============================================
# Setup .gitignore
# ============================================
echo -e "${BLUE}${LOCK} Configuring .gitignore...${NC}"

if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Environment variables and credentials
.env
*.env
.env.*
!.env.example
*credentials*
*password*

# Personal documents
*.pdf
*.docx
*.doc
*resume*
*cv*
*CV*
documents/
downloads/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
*.egg-info/
dist/
build/

# Virtual Environment
venv/
env/
ENV/

# Logs
*.log
logs/
*.log.*

# Database
*.db
*.sqlite
*.sqlite3

# Job search data (keep structure, not personal data)
job_search/*.json
!job_search/.gitkeep

# Screenshots and downloads
screenshots/
downloads/

# Browser automation
.pytest_cache/
chromedriver
geckodriver

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
*.bak
*.tmp

# Temporary files
temp/
tmp/
*.temp
EOF
    
    echo -e "${GREEN}${CHECKMARK} .gitignore created${NC}"
else
    echo -e "${YELLOW}${CHECKMARK} .gitignore already exists${NC}"
fi

echo ""

# ============================================
# Create Placeholder Files
# ============================================
echo -e "${BLUE}${FOLDER} Creating placeholder files...${NC}"

# Create .gitkeep files to preserve directory structure
touch job_search/.gitkeep
touch job_search/exports/.gitkeep
touch logs/.gitkeep
touch documents/.gitkeep
touch templates/.gitkeep

# Create initial JSON files if they don't exist
if [ ! -f "job_search/glassdoor_companies.json" ]; then
    echo '{}' > job_search/glassdoor_companies.json
fi

if [ ! -f "job_search/glassdoor_salaries.json" ]; then
    echo '{}' > job_search/glassdoor_salaries.json
fi

if [ ! -f "job_search/glassdoor_interviews.json" ]; then
    echo '{}' > job_search/glassdoor_interviews.json
fi

if [ ! -f "job_search/applications_tracker.json" ]; then
    echo '{"applications": []}' > job_search/applications_tracker.json
fi

echo -e "${GREEN}${CHECKMARK} Placeholder files created${NC}"
echo ""

# ============================================
# Install Browser Drivers (Optional)
# ============================================
echo -e "${BLUE}${WRENCH} Browser driver setup...${NC}"

read -p "Do you want to install Chrome WebDriver? [Y/n]: " INSTALL_CHROME
INSTALL_CHROME=${INSTALL_CHROME:-Y}

if [[ $INSTALL_CHROME =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}${ARROW} Installing ChromeDriver...${NC}"
    pip3 install webdriver-manager
    python3 << 'PYEOF'
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    service = Service(ChromeDriverManager().install())
    print("✓ ChromeDriver installed successfully")
except Exception as e:
    print(f"⚠ ChromeDriver installation failed: {e}")
PYEOF
fi

echo ""

# ============================================
# Configuration Wizard
# ============================================
echo -e "${BLUE}${WRENCH} Configuration Wizard${NC}"
echo "Would you like to configure your job search preferences now?"
read -p "[Y/n]: " CONFIGURE_NOW
CONFIGURE_NOW=${CONFIGURE_NOW:-Y}

if [[ $CONFIGURE_NOW =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Enter your job search preferences:${NC}"
    
    read -p "Your location (e.g., London, UK): " USER_LOCATION
    read -p "Job titles (comma-separated, e.g., Data Scientist,ML Engineer): " USER_JOBS
    read -p "Minimum salary (e.g., 80000): " USER_MIN_SALARY
    read -p "Maximum salary (e.g., 200000): " USER_MAX_SALARY
    read -p "Your email for notifications: " USER_EMAIL
    
    # Update .env with user input
    if [ -f ".env" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|LOCATION=.*|LOCATION=${USER_LOCATION}|g" .env
            sed -i '' "s|JOB_TITLES=.*|JOB_TITLES=${USER_JOBS}|g" .env
            sed -i '' "s|MIN_SALARY=.*|MIN_SALARY=${USER_MIN_SALARY}|g" .env
            sed -i '' "s|MAX_SALARY=.*|MAX_SALARY=${USER_MAX_SALARY}|g" .env
            sed -i '' "s|NOTIFICATION_EMAIL=.*|NOTIFICATION_EMAIL=${USER_EMAIL}|g" .env
        else
            # Linux
            sed -i "s|LOCATION=.*|LOCATION=${USER_LOCATION}|g" .env
            sed -i "s|JOB_TITLES=.*|JOB_TITLES=${USER_JOBS}|g" .env
            sed -i "s|MIN_SALARY=.*|MIN_SALARY=${USER_MIN_SALARY}|g" .env
            sed -i "s|MAX_SALARY=.*|MAX_SALARY=${USER_MAX_SALARY}|g" .env
            sed -i "s|NOTIFICATION_EMAIL=.*|NOTIFICATION_EMAIL=${USER_EMAIL}|g" .env
        fi
        echo -e "${GREEN}${CHECKMARK} Configuration updated${NC}"
    fi
fi

echo ""

# ============================================
# Test Installation
# ============================================
echo -e "${BLUE}${WRENCH} Testing installation...${NC}"

python3 << 'PYEOF'
import sys

def test_imports():
    tests = {
        "requests": "HTTP requests",
        "bs4": "Web scraping",
        "selenium": "Browser automation",
        "pandas": "Data processing",
        "dotenv": "Environment variables"
    }
    
    failed = []
    for module, description in tests.items():
        try:
            __import__(module)
            print(f"✓ {description} ({module})")
        except ImportError:
            print(f"✗ {description} ({module}) - FAILED")
            failed.append(module)
    
    return len(failed) == 0

if test_imports():
    print("\n✓ All core dependencies are working!")
    sys.exit(0)
else:
    print("\n⚠ Some dependencies failed. Please check the output above.")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}${CHECKMARK} Installation test passed${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed, but setup is complete${NC}"
fi

echo ""

# ============================================
# Setup Complete
# ============================================
echo -e "${GREEN}=========================================="
echo -e "${ROCKET} Setup Complete! ${ROCKET}"
echo -e "==========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "${ARROW} 1. Edit ${YELLOW}.env${NC} file with your credentials"
echo -e "${ARROW} 2. Add your resume to ${YELLOW}documents/${NC} directory"
echo -e "${ARROW} 3. Run ${YELLOW}python3 job_search_cli.py${NC} to start"
echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo -e "${ARROW} Interactive CLI: ${YELLOW}python3 job_search_cli.py${NC}"
echo -e "${ARROW} LinkedIn Search: ${YELLOW}python3 linkedin_automotion.py${NC}"
echo -e "${ARROW} Job Matching: ${YELLOW}python3 job_matcher.py${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo -e "${ARROW} README: ${YELLOW}cat README.md${NC}"
echo -e "${ARROW} .env.example: ${YELLOW}cat .env.example${NC}"
echo ""

if [[ $CREATE_VENV =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Remember to activate virtual environment:${NC}"
    echo -e "${ARROW} ${YELLOW}source venv/bin/activate${NC}"
    echo ""
fi

echo -e "${GREEN}Happy job hunting! 🎯${NC}"
echo ""
