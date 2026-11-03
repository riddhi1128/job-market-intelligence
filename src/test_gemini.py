import os
import json
import sqlite3

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

con = sqlite3.connect("data/jobs.db")
title, description = con.execute("select title, description from jobs limit 1").fetchone()
con.close()

prompt = f"""Read this job posting and reply with JSON only, with these keys:
"seniority": one of "entry", "mid", "senior", "unknown"
"required_skills": a list of skills the job requires
"summary": one short sentence

Job title: {title}
Job description: {description[:3000]}"""

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt,
    config=types.GenerateContentConfig(response_mime_type="application/json"),
)
print(title)
print(json.dumps(json.loads(response.text), indent=2))