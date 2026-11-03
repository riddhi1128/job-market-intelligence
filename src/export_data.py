import os
import sqlite3

import pandas as pd


def run():
    os.makedirs("data/exports", exist_ok=True)
    con = sqlite3.connect("data/jobs.db")

    jobs = pd.read_sql(
        """select j.source, j.job_id, j.title, j.company, j.location, j.remote,
                  j.url, j.posted_at, j.collected_on,
                  a.seniority, a.entry_friendly, a.years_experience, a.summary
           from jobs j
           left join job_ai a on a.source = j.source and a.job_id = j.job_id""",
        con,
    )
    skills = pd.read_sql(
        """select s.source, s.job_id, s.skill, j.title, j.collected_on, a.seniority
           from job_skills s
           join jobs j on j.source = s.source and j.job_id = s.job_id
           left join job_ai a on a.source = s.source and a.job_id = s.job_id""",
        con,
    )
    con.close()

    jobs.to_csv("data/exports/jobs.csv", index=False, encoding="utf-8-sig")
    skills.to_csv("data/exports/skills.csv", index=False, encoding="utf-8-sig")
    print(f"Exported {len(jobs)} jobs and {len(skills)} job-skill rows")


if __name__ == "__main__":
    run()