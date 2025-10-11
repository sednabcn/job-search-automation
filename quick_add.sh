#!/bin/bash
# Quick Add Script - Easy CLI interface for adding job search data
# Usage: ./quick_add.sh [application|contact|search]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACKING_DIR="${SCRIPT_DIR}/job_search"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to prompt for input
prompt() {
    local prompt_text="$1"
    local var_name="$2"
    local default="$3"
    
    if [ -n "$default" ]; then
        read -p "$(print_color $BLUE "$prompt_text [$default]: ")" input
        eval "$var_name=\"${input:-$default}\""
    else
        read -p "$(print_color $BLUE "$prompt_text: ")" input
        eval "$var_name=\"$input\""
    fi
}

# Function to add application
add_application() {
    print_color $GREEN "\n📝 ADD NEW APPLICATION\n"
    
    prompt "Company name" company
    prompt "Position" position
    prompt "Job URL" url
    prompt "Source (LinkedIn/Indeed/Company/etc)" source "LinkedIn"
    prompt "Status (applied/viewed/interview/etc)" status "applied"
    prompt "Resume version used" resume "default"
    prompt "Cover letter included? (y/n)" cover_letter "n"
    prompt "Notes" notes ""
    
    # Generate ID
    id="${company,,}_$(date +%s)"
    id="${id// /_}"
    
    # Generate dates
    now=$(date -Iseconds)
    followup=$(date -Iseconds -d "+7 days")
    
    # Convert cover letter to boolean
    if [[ "$cover_letter" =~ ^[Yy]$ ]]; then
        cover_bool="true"
    else
        cover_bool="false"
    fi
    
    # Generate JSON
    json=$(cat <<EOF
{
  "id": "$id",
  "company": "$company",
  "position": "$position",
  "url": "$url",
  "source": "$source",
  "resume_version": "$resume",
  "cover_letter": $cover_bool,
  "applied_date": "$now",
  "status": "$status",
  "follow_up_date": "$followup",
  "notes": "$notes",
  "timeline": [
    {
      "date": "$now",
      "event": "applied",
      "notes": "Initial application submitted"
    }
  ]
}
EOF
)
    
    echo "$json"
    return 0
}

# Function to add contact
add_contact() {
    print_color $GREEN "\n👤 ADD NEW CONTACT\n"
    
    prompt "Name" name
    prompt "Company" company ""
    prompt "Position/Title" position ""
    prompt "LinkedIn URL" linkedin ""
    prompt "Email" email ""
    prompt "How did you meet/connect?" context
    prompt "Relationship (cold/warming/warm/strong)" strength "cold"
    prompt "Tags (comma-separated)" tags ""
    prompt "Notes" notes ""
    
    # Generate ID
    id="contact_$(date +%s)"
    
    # Generate dates
    now=$(date -Iseconds)
    followup=$(date -Iseconds -d "+14 days")
    
    # Parse tags
    IFS=',' read -ra tag_array <<< "$tags"
    tag_json="["
    for i in "${tag_array[@]}"; do
        tag=$(echo "$i" | xargs) # trim whitespace
        if [ -n "$tag" ]; then
            tag_json="$tag_json\"$tag\","
        fi
    done
    tag_json="${tag_json%,}]"
    
    # Generate JSON
    json=$(cat <<EOF
{
  "id": "$id",
  "name": "$name",
  "company": "$company",
  "position": "$position",
  "linkedin_url": "$linkedin",
  "email": "$email",
  "connection_context": "$context",
  "relationship_strength": "$strength",
  "tags": $tag_json,
  "last_contact": "$now",
  "next_followup": "$followup",
  "interactions": [
    {
      "date": "$now",
      "type": "linkedin_message",
      "notes": "Initial connection",
      "sentiment": "positive"
    }
  ],
  "notes": "$notes"
}
EOF
)
    
    echo "$json"
    return 0
}

# Function to add saved search
add_search() {
    print_color $GREEN "\n🔍 ADD SAVED SEARCH\n"
    
    prompt "Search name" name
    prompt "Keywords (comma-separated)" keywords
    prompt "Location (leave empty for remote)" location ""
    prompt "Remote work? (y/n)" remote "y"
    prompt "Job boards (comma-separated: linkedin,indeed,glassdoor)" boards "linkedin,indeed"
    prompt "Minimum salary" salary ""
    prompt "Experience level (entry/mid/senior/lead)" experience "mid"
    
    # Generate ID
    id="search_$(date +%s)"
    
    # Parse keywords
    IFS=',' read -ra kw_array <<< "$keywords"
    kw_json="["
    for i in "${kw_array[@]}"; do
        kw=$(echo "$i" | xargs)
        if [ -n "$kw" ]; then
            kw_json="$kw_json\"$kw\","
        fi
    done
    kw_json="${kw_json%,}]"
    
    # Parse boards
    IFS=',' read -ra board_array <<< "$boards"
    board_json="["
    for i in "${board_array[@]}"; do
        board=$(echo "$i" | xargs)
        if [ -n "$board" ]; then
            board_json="$board_json\"$board\","
        fi
    done
    board_json="${board_json%,}]"
    
    # Convert remote to boolean
    if [[ "$remote" =~ ^[Yy]$ ]]; then
        remote_bool="true"
    else
        remote_bool="false"
    fi
    
    # Handle salary
    if [ -z "$salary" ]; then
        salary_json="null"
    else
        salary_json="$salary"
    fi
    
    # Generate dates
    now=$(date -Iseconds)
    
    # Generate JSON
    json=$(cat <<EOF
{
  "id": "$id",
  "name": "$name",
  "keywords": $kw_json,
  "location": "$location",
  "remote": $remote_bool,
  "boards": $board_json,
  "min_salary": $salary_json,
  "experience_level": "$experience",
  "created": "$now",
  "last_checked": null,
  "jobs_found": 0
}
EOF
)
    
    echo "$json"
    return 0
}

# Main script
main() {
    print_color $BLUE "═══════════════════════════════════════"
    print_color $BLUE "   Job Search Quick Add CLI"
    print_color $BLUE "═══════════════════════════════════════\n"
    
    # Check if json_updater.py exists
    if [ ! -f "${SCRIPT_DIR}/job_search/json_updater.py" ]; then
        print_color $RED "❌ Error: json_updater.py not found!"
        echo "   Expected location: ${SCRIPT_DIR}/job_search/json_updater.py"
        exit 1
    fi
    
    # Determine data type
    if [ -n "$1" ]; then
        data_type="$1"
    else
        print_color $YELLOW "What would you like to add?\n"
        echo "  1) Application"
        echo "  2) Contact"
        echo "  3) Saved Search"
        echo ""
        read -p "Enter choice (1-3): " choice
        
        case $choice in
            1) data_type="application" ;;
            2) data_type="contact" ;;
            3) data_type="search" ;;
            *)
                print_color $RED "Invalid choice!"
                exit 1
                ;;
        esac
    fi
    
    # Generate JSON based on type
    case $data_type in
        application|app|1)
            json=$(add_application)
            type_name="application"
            ;;
        contact|person|2)
            json=$(add_contact)
            type_name="contact"
            ;;
        search|3)
            json=$(add_search)
            type_name="search"
            ;;
        *)
            print_color $RED "Unknown type: $data_type"
            echo "Usage: $0 [application|contact|search]"
            exit 1
            ;;
    esac
    
    # Show preview
    print_color $YELLOW "\n📋 Generated JSON:\n"
    echo "$json" | python3 -m json.tool
    
    # Confirm
    echo ""
    read -p "$(print_color $BLUE 'Add this entry? (y/n): ')" confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_color $YELLOW "❌ Cancelled"
        exit 0
    fi
    
    # Process
    print_color $BLUE "\n⏳ Processing..."
    
    result=$(echo "$json" | python3 "${SCRIPT_DIR}/job_search_system/json_updater.py" "$type_name" 2>&1)
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "\n✅ Success!"
        echo "$result" | python3 -m json.tool
        
        # Ask about committing
        echo ""
        read -p "$(print_color $BLUE 'Commit and push to GitHub? (y/n): ')" commit_confirm
        
        if [[ "$commit_confirm" =~ ^[Yy]$ ]]; then
            cd "$SCRIPT_DIR"
            git add job_search/
            git commit -m "Add ${type_name}: $(date '+%Y-%m-%d %H:%M')"
            git push
            print_color $GREEN "✅ Committed and pushed!"
        else
            print_color $YELLOW "⚠️  Don't forget to commit manually:"
            echo "   cd $SCRIPT_DIR"
            echo "   git add job_search/"
            echo "   git commit -m 'Add ${type_name}'"
            echo "   git push"
        fi
    else
        print_color $RED "\n❌ Error:"
        echo "$result"
        exit 1
    fi
    
    # Ask if want to add more
    echo ""
    read -p "$(print_color $BLUE 'Add another entry? (y/n): ')" another
    
    if [[ "$another" =~ ^[Yy]$ ]]; then
        exec "$0"
    fi
    
    print_color $GREEN "\n✅ All done!\n"
}

# Run main
main "$@"
