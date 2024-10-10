import httpx
from arango import ArangoClient
from prefect import task, flow
from prefect.blocks.system import Secret
from prefect.client.schemas.schedules import CronSchedule

def setup_progress_client():
  base_url='http://api:8000'
  progress_api_token = Secret.load('progress-api-token').get()
  headers=dict(Autorization=f'Bearer: {progress_api_token}')
  return httpx.Client(base_url=base_url, headers=headers)

def connect_to_progress_db():
  try:
    with open('/run/secrets/progress_api_db_pwd') as secret:
      username = 'progress_api'
      progress_db_password = secret.read().rstrip('\n')
  except FileNotFoundError:
    username = 'root'
    progress_db_password = ''

  client = ArangoClient(hosts="http://db:8529")
  db = client.db('PROGRESS_PROD', username=username, password=progress_db_password)

  return db


db = connect_to_progress_db()

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
def pause_job(api, job_data):
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
  job_key = job_data['_key']

  print(f'Pausing job {job_key}...')

  event_data = dict(
    event_type = 'JOB_PAUSED_OFFLINE',
    job_key = job_key,
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
def main():
  """
  Pause jobs that have been offline for more seconds than indicated in the `max_offline` parameter of the job
  """
  jobs_to_pause = check_offline_jobs()
  with setup_progress_client() as api:
    for job in jobs_to_pause:
      pause_job(api, job)


schedule = CronSchedule(cron="0 * * * *")
