import secrets
import traceback

from arango import ArangoClient


# ————————————————————————————
# Setup DB
# ————————————————————————————
# Run a disposable container to bootstrap the db_data volume
print('Creating DB users...')

client = ArangoClient(hosts='http://localhost:8529')

def get_secret(name):
  with open(f'/run/secrets/{name}') as secret
    return secret.read()

with client.db(username='root', password='').begin_batch_execution() as sys_db:

  # ————————————————————————————
  # Create DB Users
  # ————————————————————————————
  db_users = {
    'progress_dev': get_secret('progress_dev_db_pwd'),
    'progress_api': get_secret('progress_api_db_pwd'),
    'customer':'customer'
  }

  # TODO: Check if users are present
  for u, pwd in db_users:
    sys_db.create_user(username=u, password=pwd)
    users[u] = pwd
    print('Created user', u)

  print('Done\n\nCreating DBs...')
  # ————————————————————————————
  # Create DBs
  # ————————————————————————————
  dbs = [
    'PROGRESS_DEV',
    'PROGRESS_TEST',
    'PROGRESS_PROD'
  ]

  for db in dbs:
    sys_db.create_database(db)
    print('Created DB', db)

  print('Done\n\nSetting user permissions...', end=' ')

  # ————————————————————————————
  # Set permissions
  # ————————————————————————————
  sys_db.update_permission(username='progress_dev', permission='rw', database='*')
  sys_db.update_permission(username='progress_api', permission='rw', database='*')
  sys_db.update_permission(username='customer', permission='ro', database='*')

  print('Done\n\nCreating collections...', end=' ')


# ————————————————————————————
# Create Collections
# ————————————————————————————
collections = [
  'Batch',
  'BatchTimeRecord',
  'Config',
  'Department',
  'Event',
  'Job',
  'Operation',
  'Phase',
  'Product',
  'ProductionItem',
  'Queue',
  'requires',
  'Serial',
  'Site',
  'Step',
  'StepExecutionData',
  'Token',
  'User',
  'UserSession',
  'WIP',
  'WorkOrder',
  'WorkSession'
]

db_handles = [client.db(database, username='root', password='') for database in dbs]

for dbh in db_handles:
  with dbh.begin_batch_execution(return_result=True) as batch:
    for c in collections:
      # if collection name starts with a lowercase letter it's an edge collection
      batch.create_collection(name=c, edge=c[0].islower())
    print('Created collections in db ', dbh.db_name)

"""
INSERT HERE DEFAULT CONFIGS
- Default user
- Default operation and parameters
- Default site
- Default queues
- ...
"""
