import json
import os
import sqlite3
from collections import Counter

import pandas as pd

MIN_SKILLS = 3  # ignore jobs where fewer than 3 skills were found


def load_profile(path="agents/my_profile.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run():
    mine = set(load_profile()["skills"])

    con = sqlite3.connect("data/jobs.db")
    jobs = pd.read_sql("select source, job_id, title, company, location, url from jobs", con)
    skills = pd.read_sql("select source, job_id, skill from job_skills", con)
    con.close()

    needed = skills.groupby(["source", "job_id"])["skill"].apply(set).to_dict()

    rows = []
    gap_counter = Counter()
    for _, job in jobs.iterrows():
        required = needed.get((job["source"], job["job_id"]), set())
        if len(required) < MIN_SKILLS:
            continue
        have = required & mine
        missing = required - mine
        gap_counter.update(missing)
        rows.append({
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "url": job["url"],
            "match_percent": round(100 * len(have) / len(required)),
            "skills_you_have": ", ".join(sorted(have)),
            "skills_missing": ", ".join(sorted(missing)),
        })

    if not rows:
        print("No jobs with enough skills found yet.")
        return

    matches = pd.DataFrame(rows).sort_values("match_percent", ascending=False)
    gaps = pd.DataFrame(gap_counter.most_common(10), columns=["skill", "jobs_asking"])

    os.makedirs("data/exports", exist_ok=True)
    matches.to_csv("data/exports/matches.csv", index=False, encoding="utf-8-sig")
    gaps.to_csv("data/exports/skill_gaps.csv", index=False, encoding="utf-8-sig")

    print(f"Jobs matched: {len(matches)}")
    print("\nBest matches:")
    print(matches.head(5)[["title", "company", "match_percent"]].to_string(index=False))
    print("\nSkills you are missing most:")
    print(gaps.to_string(index=False))


if __name__ == "__main__":
    run()