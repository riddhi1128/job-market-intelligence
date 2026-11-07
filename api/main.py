import os
import sqlite3

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

DB_PATH = os.getenv("DB_PATH", "data/jobs.db")
MATCHES_PATH = os.getenv("MATCHES_PATH", "data/exports/matches.csv")
REPORT_PATH = os.getenv("REPORT_PATH", "data/exports/weekly_report.md")

app = FastAPI(
    title="Job Market Intelligence API",
    description="Skills in demand, entry-level jobs and personal matches for data roles.",
)


def query(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    con.close()
    return rows


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/skills/top")
def top_skills(limit: int = Query(10, ge=1, le=50)):
    return query(
        "select skill, count(*) as jobs from job_skills group by skill order by jobs desc limit ?",
        (limit,),
    )


@app.get("/jobs")
def jobs(
    entry_only: bool = False,
    remote: bool | None = None,
    search: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    sql = """select j.title, j.company, j.location, j.remote, j.url,
                    a.seniority, a.entry_friendly, a.summary
             from jobs j
             left join job_ai a on a.source = j.source and a.job_id = j.job_id
             where 1 = 1"""
    params = []
    if entry_only:
        sql += " and a.entry_friendly = 1"
    if remote is not None:
        sql += " and j.remote = ?"
        params.append(int(remote))
    if search:
        sql += " and lower(j.title) like ?"
        params.append(f"%{search.lower()}%")
    sql += " order by j.posted_at desc limit ?"
    params.append(limit)
    return query(sql, tuple(params))


@app.get("/matches")
def matches(limit: int = Query(10, ge=1, le=50)):
    if not os.path.exists(MATCHES_PATH):
        raise HTTPException(status_code=404, detail="No matches yet. Run the pipeline first.")
    df = pd.read_csv(MATCHES_PATH).head(limit).fillna("")
    return df.to_dict("records")


@app.get("/report")
def report():
    if not os.path.exists(REPORT_PATH):
        raise HTTPException(status_code=404, detail="No report yet. Run the pipeline first.")
    with open(REPORT_PATH, encoding="utf-8") as f:
        return {"report": f.read()}