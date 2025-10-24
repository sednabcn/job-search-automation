#!/usr/bin/env python3
import re
from pathlib import Path

workflow_file = Path('.github/workflows/job-application-multiplatform.yml')
content = workflow_file.read_text()

# Pattern to find old-style commits
old_commit_pattern = r'''(\s+)- name: Commit ([^\n]+)\n\s+run: \|\n\s+git config user\.name[^\n]+\n\s+git config user\.email[^\n]+\n\s+\n\s+git add ([^\n]+)\n\s+\n\s+git diff[^\n]+\n\s+git commit -m "([^"]+)"[^\n]*\n\s+\n\s+git push[^\n]*'''

def replacement(match):
    indent = match.group(1)
    name = match.group(2)
    files = match.group(3)
    message = match.group(4)
    
    return f'''{indent}- name: Commit {name}
{indent}  uses: ./.github/actions/safe-git-push
{indent}  with:
{indent}    commit-message: "{message}"
{indent}    files: "{files}"'''

new_content = re.sub(old_commit_pattern, replacement, content, flags=re.MULTILINE)

if new_content != content:
    workflow_file.write_text(new_content)
    print("✅ Updated workflow file")
    print(f"   Changes made: {content.count('git config user.name') - new_content.count('git config user.name')}")
else:
    print("⚠️  No changes needed")
