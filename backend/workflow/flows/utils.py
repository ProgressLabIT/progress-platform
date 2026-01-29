import httpx
import os
from arango import ArangoClient
from prefect.blocks.system import Secret

def connect_to_progress_db():
  try:
    with open('/run/secrets/progress_api_db_pwd') as secret:
      username = 'progress_api'
      progress_db_password = secret.read().rstrip('\n')
      url = os.getenv('ARANGO_URL', 'http://db:8529')
  except FileNotFoundError:
    username = 'root'
    progress_db_password = ''
    url = os.getenv('ARANGO_URL', 'http://localhost:8529')

  client = ArangoClient(hosts=url)
  db = client.db('PROGRESS_PROD', username=username, password=progress_db_password)

  return db


def setup_progress_client():
  base_url=os.getenv('PROGRESS_API_URL', 'http://api:8000')
  progress_api_token = Secret.load('progress-api-token').get()
  headers=dict(Autorization=f'Bearer: {progress_api_token}')
  return httpx.Client(base_url=base_url, headers=headers)
