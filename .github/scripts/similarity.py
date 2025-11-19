import os
import json
import numpy as np
from github import Github
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

# --- GitHub context ---
issue_number = int(os.environ["ISSUE_NUMBER"])
repo_name = os.environ["REPO"]
gh_token = os.environ["GH_TOKEN"]
openai_key = os.environ["OPENAI_API_KEY"]

# --- Connect to GitHub ---
gh = Github(gh_token)
repo = gh.get_repo(repo_name)
issue = repo.get_issue(number=issue_number)

# --- OpenAI client ---
client = OpenAI(api_key=openai_key)

# --- DB paths ---
text_db_path = ".github/issue_texts.json"
embeddings_db_path = ".github/issue_embeddings.json"

# Load DBs
if os.path.exists(text_db_path):
    text_db = json.load(open(text_db_path, "r"))
else:
    text_db = {}

if os.path.exists(embeddings_db_path):
    embeddings_db = json.load(open(embeddings_db_path, "r"))
else:
    embeddings_db = {}

# --- Extract current issue text ---
current_text = (issue.title or "") + "\n" + (issue.body or "")

# --- Helper: embed text ---
def embed(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# If no previous data → store and exit
if len(embeddings_db) == 0:
    current_emb = embed(current_text)
    embeddings_db[str(issue_number)] = current_emb
    text_db[str(issue_number)] = current_text
    json.dump(embeddings_db, open(embeddings_db_path, "w"))
    json.dump(text_db, open(text_db_path, "w"))
    print("First issue stored — no comparisons made.")
    exit(0)

# --- Compute embedding for current issue ---
current_emb = np.array(embed(current_text))

# --- Compare to all existing issues ---
matches = []
THRESHOLD = 0.80  # LLM embeddings are much stronger

for num, emb in embeddings_db.items():
    emb = np.array(emb)
    score = cosine_similarity([current_emb], [emb])[0][0]
    if score >= THRESHOLD:
        matches.append((num, score))

# --- Comment results ---
if matches:
    matches = sorted(matches, key=lambda x: x[1], reverse=True)
    msg = "### 🔍 AI detected related initiatives\n\n"
    for num, score in matches:
        msg += f"- Issue #{num} — similarity **{score:.2f}**\n"
    issue.create_comment(msg)

# --- Store this issue ---
embeddings_db[str(issue_number)] = current_emb.tolist()
text_db[str(issue_number)] = current_text

json.dump(embeddings_db, open(embeddings_db_path, "w"))
json.dump(text_db, open(text_db_path, "w"))