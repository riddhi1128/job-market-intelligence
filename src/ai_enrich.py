import json
import os
import sqlite3
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
MAX_JOBS_PER_RUN = 20
PAUSE_SECONDS = 7

PROMPT = """Read this job posting and reply with JSON only, using these keys:
"seniority": one of "entry", "mid", "senior", "unknown"
"entry_friendly": true if a person with 0 to 2 years of experience could reasonably apply, else false
"years_experience": the minimum years of experience required, as a whole number, or null if not stated
"required_skills": a list of up to 10 required skills, short lowercase names
"summary": one short sentence about the role

Job title: {title}
Job description: {description}"""


def ask(client, title, description):
    response = client.models.generate_content(
        model=MODEL,
        contents=PROMPT.format(title=title, description=(description or "")[:3000]),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def run():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    con = sqlite3.connect("data/jobs.db")
    con.execute(
        """create table if not exists job_ai (
            source text, job_id text, seniority text, entry_friendly integer,
            years_experience integer, required_skills text, summary text,
            model text, processed_at text,
            primary key (source, job_id))"""
    )

    todo = con.execute(
        """select source, job_id, title, description from jobs j
           where not exists (select 1 from job_ai a
                             where a.source = j.source and a.job_id = j.job_id)
           order by posted_at desc limit ?""",
        (MAX_JOBS_PER_RUN,),
    ).fetchall()
    print(f"{len(todo)} new jobs to read")

    for source, job_id, title, description in todo:
        try:
            r = ask(client, title, description)
        except Exception as e:
            print(f"Stopped at '{title}': {e}")
            break
        con.execute(
            "insert or replace into job_ai values (?,?,?,?,?,?,?,?,?)",
            (
                source,
                job_id,
                r.get("seniority"),
                int(bool(r.get("entry_friendly"))),
                to_int(r.get("years_experience")),
                ", ".join(r.get("required_skills") or []),
                r.get("summary"),
                MODEL,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        con.commit()
        print(f"{title}: {r.get('seniority')}")
        time.sleep(PAUSE_SECONDS)

    con.close()


if __name__ == "__main__":
    run()