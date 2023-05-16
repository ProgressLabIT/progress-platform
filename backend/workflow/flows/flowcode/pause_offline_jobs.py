from datetime import timedelta

import httpx
from arango import ArangoClient
from prefect import task, flow, get_run_logger


client = ArangoClient(hosts="http://db:8529")
db = client.db('PROGRESS_TEST', username='root', password='')

httpx_params = dict(
    # proxies={ "all://progress.localhost": "http://localhost:80" },
    base_url='http://api:8000'
)

query = """
  FOR j IN Job
  FILTER
    j.active
    && j.parameters.max_offline > 0
    && DATE_DIFF(DATE_TIMESTAMP(j.last_online), DATE_NOW(), 's', true) > j.parameters.max_offline
  RETURN j
"""

@task
def check_offline_jobs() -> list:
  print('Checking offline jobs...')
  result = [_ for _ in db.aql.execute(query)]
  print(f'Found { len(result) } jobs to pause')
  return result

@task
def pause_job(job_data):
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
  print(f'Pausing job {job_key}...')
  with httpx.Client(**httpx_params) as api:
    event_data = dict(
      event_type = 'JOB_PAUSED_OFFLINE',
      job_key = job_data['_key'],
      work_session_end = job_data['last_online'],
      user_key = 'wf:pause_offline_jobs',
      user_session_key = 'wf',
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


@flow(name="Pause offline jobs", log_prints=True)
"""
Pause jobs that have been offline for more seconds than indicated in the `max_offline` parameter of the job
"""
def pause_offline_jobs():
  jobs_to_pause = check_offline_jobs()
  for job_key in jobs_to_pause:
    pause_job(job_key)


