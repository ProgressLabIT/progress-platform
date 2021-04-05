from datetime import timedelta

from prefect import task, Flow
from prefect.schedules import IntervalSchedule

from utils.db import db


query = """
  FOR j IN Job
  FILTER
    j.active
    && j.max_online > 0
    && DATE_DIFF(DATE_NOW(), j.last_online, 'i', true) > j.max_online
  RETURN j._key
"""

schedule = IntervalSchedule(interval=timedelta(minutes=1))

@task
def check_offline_jobs():
  sessions_to_close = db.aql.execute('query').next()


@task
def pause_job(job_key):
  """
  Use the event API to pause jobs
  e.g.
  event_data = dict(
    event_type = 'JOB_PAUSED',
    job_key = job_key,
    reason = "Exceeded max offline time allowed"
  )
  api.event(event_data)
  """


with Flow("pause_offline_jobs", schedule) as flow:
  print("Checking offline jobs...")
  jobs_to_pause = check_offline_jobs
  print(f"Found {len(jobs_to_pause)} jobs to pause: {[j for j in jobs_to_pause]}")
  pause_jobs.map(jobs_to_pause)

flow.run()
