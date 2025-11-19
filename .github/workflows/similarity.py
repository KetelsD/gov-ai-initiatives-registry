import os
import json
from github import Github

# --- Setup variables ---
issue_number = int(os.environ["ISSUE_NUMBER"])
repo_name = os.environ["REPO"]
token = os.environ["GH_TOKEN"]

# --- Connect to GitHub ---
g = Github(token)
repo = g.get_repo(repo_name)
issue = repo.get_issue(number=issue_number)

# --- Create/Load "database" of issues ---
db_path = ".github/issue_db.json"

if os.path.exists(db_path):
    db = json.load(open(db_path, "r"))
else:
    db = {}

# --- Simple fake similarity check ---
current_text = (issue.title or "") + "\n" + (issue.body or "")

similar_issues = []
for num, text in db.items():
    if text.strip() == current_text.strip():
        similar_issues.append(num)

# --- Post a comment if duplicates found ---
if similar_issues:
    message = "### 🔍 Possible duplicates found (test mode):\n"
    for num in similar_issues:
        message += f"- Issue #{num}\n"
    issue.create_comment(message)

# --- Store current issue text ---
db[str(issue_number)] = current_text
json.dump(db, open(db_path, "w"))