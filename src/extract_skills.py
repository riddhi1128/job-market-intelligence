import re
import sqlite3

import pandas as pd

# skill name -> word pattern to look for
SKILLS = {
    "python": r"\bpython\b",
    "sql": r"\b(?:sql|mysql|postgresql|postgres|t-sql)\b",
    "power bi": r"power\s?bi",
    "tableau": r"\btableau\b",
    "excel": r"\bexcel\b",
    "looker": r"\blooker\b",
    "pandas": r"\bpandas\b",
    "numpy": r"\bnumpy\b",
    "scikit-learn": r"scikit-?learn|sklearn",
    "tensorflow": r"\btensorflow\b",
    "pytorch": r"\bpytorch\b",
    "machine learning": r"machine learning|\bml\b",
    "deep learning": r"deep learning",
    "nlp": r"\bnlp\b|natural language",
    "llm": r"\bllms?\b|large language model|generative ai|genai",
    "statistics": r"statistic",
    "spark": r"\bspark\b|pyspark",
    "airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "kafka": r"\bkafka\b",
    "snowflake": r"\bsnowflake\b",
    "databricks": r"\bdatabricks\b",
    "etl": r"\betl\b|\belt\b|data pipeline",
    "aws": r"\baws\b|amazon web services",
    "azure": r"\bazure\b",
    "gcp": r"\bgcp\b|google cloud",
    "docker": r"\bdocker\b",
    "git": r"\bgit\b|github",
    "data visualization": r"data visuali[sz]ation|dashboard",
    "a/b testing": r"a/b test|experimentation",
}


def find_skills(text):
    text = (text or "").lower()
    return [skill for skill, pattern in SKILLS.items() if re.search(pattern, text)]


def run():
    con = sqlite3.connect("data/jobs.db")
    jobs = pd.read_sql("select source, job_id, title, description, tags from jobs", con)

    rows = []
    for _, job in jobs.iterrows():
        text = f"{job['title']} {job['tags']} {job['description']}"
        for skill in find_skills(text):
            rows.append({"source": job["source"], "job_id": job["job_id"], "skill": skill})

    skills_df = pd.DataFrame(rows, columns=["source", "job_id", "skill"])
    skills_df.to_sql("job_skills", con, if_exists="replace", index=False)

    top = pd.read_sql(
        "select skill, count(*) as jobs from job_skills group by skill order by jobs desc limit 15",
        con,
    )
    print(f"Jobs checked: {len(jobs)}")
    print(top.to_string(index=False))
    con.close()


if __name__ == "__main__":
    run()