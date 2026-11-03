import os
import json
import time
from datetime import date

import requests

HEADERS = {"User-Agent": "job-market-intelligence-portfolio-project"}


def fetch_remotive():
    url = "https://remotive.com/api/remote-jobs"
    response = requests.get(url, params={"category": "data"}, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()["jobs"]


def fetch_arbeitnow(pages=3):
    jobs = []
    for page in range(1, pages + 1):
        url = "https://www.arbeitnow.com/api/job-board-api"
        response = requests.get(url, params={"page": page}, headers=HEADERS, timeout=30)
        response.raise_for_status()
        jobs.extend(response.json()["data"])
        time.sleep(1)
    return jobs


def save_raw(source, jobs):
    os.makedirs("data/raw", exist_ok=True)
    path = f"data/raw/{source}_{date.today()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    print(f"{source}: saved {len(jobs)} jobs to {path}")


if __name__ == "__main__":
    save_raw("remotive", fetch_remotive())
    save_raw("arbeitnow", fetch_arbeitnow())