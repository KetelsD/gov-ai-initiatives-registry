import os
import json
from github import Github
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Setup GitHub variables ---
issue_number = int(os.environ["ISSUE_NUMBER"])
repo_name = os.environ["REPO"]
token = os.environ["GH_TOKEN"]

# --- Connect to GitHub ---
gh = Github(token)
repo = gh.get_repo(repo_name)
issue = repo.get_issue(number=issue_number)

# --- Database path ---
db_path = ".github/issue_db.json"

# Load DB
if os.path.exists(db_path):
    db = json.load(open(db_path, "r"))
else:
    db = {}

# --- Current issue text ---
current_text = (issue.title or "") + "\n" + (issue.body or "")

# If no previous issues, just store and exit
if len(db) == 0:
    db[str(issue_number)] = current_text
    json.dump(db, open(db_path, "w"))
    print("No previous issues — stored current issue only.")
    exit(0)

# --- Build corpus for TF-IDF ---
corpus = [current_text]  # index 0 = new issue
index_map = ["current"]

for num, text in db.items():
    corpus.append(text)
    index_map.append(num)

# --- TF-IDF ---
vectorizer = TfidfVectorizer(stop_words="english")
vectors = vectorizer.fit_transform(corpus)

# Compare index 0 to all others
similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

# Threshold
THRESHOLD = 0.55
matches = []

for score, num in zip(similarities, index_map[1:]):
    if score > THRESHOLD:
        matches.append((num, score))

# --- Comment results ---
if matches:
    matches = sorted(matches, key=lambda x: x[1], reverse=True)
    message = "### 🔍 Potential related AI project ideas detected\n\n"
    for num, score in matches:
        message += f"- Issue #{num} — similarity **{score:.2f}**\n"
    issue.create_comment(message)

# Update DB
db[str(issue_number)] = current_text
json.dump(db, open(db_path, "w"))