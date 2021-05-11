from datetime import timedelta

import httpx
from arango import ArangoClient
from prefect import task, Flow
from prefect.schedules import IntervalSchedule

client = ArangoClient(hosts="http://db:8529")
db = client.db('PROGRESS_TEST', username='root', password='')

query = """
  FOR j IN Job
  FILTER
    j.active
    && j.parameters.max_offline > 0
    && DATE_DIFF(j.last_online, DATE_NOW(), 'i', true) > j.parameters.max_offline
  RETURN j._key
"""

schedule = IntervalSchedule(interval=timedelta(minutes=1))

@task
def check_offline_jobs() -> list:
  result = [_ for _ in db.aql.execute(query)]
  print(result)
  return result

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
  with httpx.Client(base_url='http://api:8000') as api:
    print(f'Pausing job {job_key}...')
    event_data = dict(
      event_type = 'JOB_PAUSED_OFFLINE',
      job_key = job_key,
      user_key = 'wf:pause_offline_jobs',
      description = "Exceeded max offline time allowed"
    )
    try:
      print('Calling API...', end="")
      r = api.post('/event', json=event_data)
      print('Response: ', r.json())
      if r.status_code == 200:
        print(f"Job {job_key} paused.")
    except Exception as e:
      print(f'Error while pausing job {job_key}: {e}')


if __name__ == "__main__":
  with Flow("pause_offline_jobs", schedule) as flow:
    print("Checking offline jobs...")
    jobs_to_pause = check_offline_jobs()
    print(jobs_to_pause)
    # print(fx"Found {jobs_to_pause} jobs to pause: {[j for j in jobs_to_pause]}")
    pause_job.map(jobs_to_pause)

  flow.run()
