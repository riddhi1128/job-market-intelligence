import glob
import html
import json
import os
import re
import sqlite3
from datetime import datetime, timezone

import pandas as pd

# A job is kept if its title has one of these words
PATTERN = r"\b(?:data|analytics|analyst|machine learning|ml|bi|business intelligence|scientist|ai)\b"


def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def file_date(path):
    return os.path.basename(path).replace(".json", "").split("_")[-1]


def load_remotive(path):
    rows = []
    for j in json.load(open(path, encoding="utf-8")):
        rows.append({
            "source": "remotive",
            "job_id": str(j.get("id")),
            "title": j.get("title"),
            "company": j.get("company_name"),
            "location": j.get("candidate_required_location"),
            "remote": True,
            "description": clean_text(j.get("description")),
            "url": j.get("url"),
            "posted_at": j.get("publication_date"),
            "tags": ", ".join(j.get("tags") or []),
            "collected_on": file_date(path),
        })
    return rows


def load_arbeitnow(path):
    rows = []
    for j in json.load(open(path, encoding="utf-8")):
        posted = datetime.fromtimestamp(j["created_at"], tz=timezone.utc).isoformat()
        rows.append({
            "source": "arbeitnow",
            "job_id": j.get("slug"),
            "title": j.get("title"),
            "company": j.get("company_name"),
            "location": j.get("location"),
            "remote": bool(j.get("remote")),
            "description": clean_text(j.get("description")),
            "url": j.get("url"),
            "posted_at": posted,
            "tags": ", ".join(j.get("tags") or []),
            "collected_on": file_date(path),
        })
    return rows


if __name__ == "__main__":
    rows = []
    for p in glob.glob("data/raw/remotive_*.json"):
        rows += load_remotive(p)
    for p in glob.glob("data/raw/arbeitnow_*.json"):
        rows += load_arbeitnow(p)

    df = pd.DataFrame(rows)
    print(f"Raw jobs: {len(df)}")

    df = df[df["title"].str.contains(PATTERN, case=False, regex=True, na=False)]
    df = df.sort_values("collected_on").drop_duplicates(subset=["source", "job_id"])
    print(f"Data-related jobs kept: {len(df)}")

    con = sqlite3.connect("data/jobs.db")
    df.to_sql("jobs", con, if_exists="replace", index=False)
    con.close()
    print("Saved to data/jobs.db (table: jobs)")