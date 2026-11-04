import os

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import json
from datetime import date

import pandas as pd
from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def build_data_text():
    with open("agents/my_profile.json", encoding="utf-8") as f:
        profile = json.load(f)
    matches = pd.read_csv("data/exports/matches.csv").head(8)
    gaps = pd.read_csv("data/exports/skill_gaps.csv")

    text = "Candidate skills: " + ", ".join(profile["skills"]) + "\n\n"
    text += "Best matching jobs (title, company, match %, missing skills):\n"
    for _, r in matches.iterrows():
        missing = r["skills_missing"] if isinstance(r["skills_missing"], str) else "none"
        text += f"- {r['title']} at {r['company']}: {r['match_percent']}%, missing: {missing}\n"
    text += "\nSkills missing most often (skill, number of jobs asking):\n"
    for _, r in gaps.iterrows():
        text += f"- {r['skill']}: {r['jobs_asking']}\n"
    return text


def run():
    llm = LLM(
        model=f"gemini/{MODEL}",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2,
    )

    analyst = Agent(
        role="Career Skills Analyst",
        goal="Decide which skills the candidate should learn first, using only the data given",
        backstory="You help entry-level data candidates choose what to learn next. You never invent data.",
        llm=llm,
        allow_delegation=False,
    )
    writer = Agent(
        role="Weekly Report Writer",
        goal="Write a short, clear weekly summary in plain language",
        backstory="You write brief reports that a busy recruiter or student can read in one minute.",
        llm=llm,
        allow_delegation=False,
    )

    analysis_task = Task(
        description=(
            "Read this data and rank the 3 most valuable skills for the candidate to learn next. "
            "Give one sentence of reasoning for each, based only on the numbers.\n\n"
            + build_data_text()
        ),
        expected_output="A numbered list of 3 skills, one sentence each.",
        agent=analyst,
    )
    report_task = Task(
        description=(
            "Write a weekly summary of under 150 words. First mention the best matching jobs, "
            "then the 3 skills to learn, using the analyst's list."
        ),
        expected_output="A short markdown report with a heading.",
        agent=writer,
        context=[analysis_task],
    )

    crew = Crew(
        agents=[analyst, writer],
        tasks=[analysis_task, report_task],
        process=Process.sequential,
    )
    result = str(crew.kickoff())

    os.makedirs("data/exports", exist_ok=True)
    with open("data/exports/weekly_report.md", "w", encoding="utf-8") as f:
        f.write(f"_Generated on {date.today()}_\n\n{result}\n")
    print(result)


if __name__ == "__main__":
    run()