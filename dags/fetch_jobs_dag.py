import sys
from datetime import datetime

from airflow.sdk import dag, task

sys.path.append("/opt/airflow")


@dag(
    dag_id="fetch_jobs_daily",
    schedule="@daily",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    tags=["job-market"],
)
def fetch_jobs_daily():
    @task
    def fetch_and_save():
        from src.fetch_jobs import fetch_remotive, fetch_arbeitnow, save_raw

        save_raw("remotive", fetch_remotive())
        save_raw("arbeitnow", fetch_arbeitnow())

    @task
    def clean():
        from src.clean_jobs import run

        run()

    @task
    def extract_skills():
        from src.extract_skills import run

        run()

    @task
    def ai_enrich():
        from src.ai_enrich import run

        run()

    @task
    def export_data():
        from src.export_data import run

        run()

    @task
    def match_jobs():
        from src.match_jobs import run

        run()

    @task
    def career_report():
        from agents.career_crew import run

        run()

    fetched = fetch_and_save()
    cleaned = clean()
    fetched >> cleaned >> extract_skills() >> ai_enrich() >> export_data() >> match_jobs() >> career_report()


fetch_jobs_daily()