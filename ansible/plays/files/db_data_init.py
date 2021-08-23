import secrets
import traceback

import docker as d
from arango import ArangoClient


# ————————————————————————————
# Setup DB
# ————————————————————————————
# Run a disposable container to bootstrap the db_data volume
print('Creating DB users...')


client = ArangoClient(hosts='http://localhost:8529')
sys_db = client.db(username='root', password='')

# ————————————————————————————
# Create DB Users
# ————————————————————————————
users = {
  'progress_dev':'',
  'progress_api':'',
  'customer':''
}

# TODO: Check if users are present
for u in users:
  pwd = secrets.token_hex(6)
  sys_db.create_user(username=u, password=pwd)
  users[u] = pwd
  print('Created user ', u)

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
  print('Created DB ', db)

print('Done\n\nSetting user permissions...', end=' ')

# ————————————————————————————
# Set permissions
# ————————————————————————————
sys_db.update_permission(username='progress_dev', permission='rw', database='*')
sys_db.update_permission(username='progress_api', permission='rw', database='PROGRESS_PROD')
sys_db.update_permission(username='customer', permission='ro', database='PROGRESS_PROD')

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

db_handles = [client.db(db, username='root', password='') for db in dbs]

for db in db_handles:
  for c in collections:
    db.create_collection(name=c, edge=c[0].islower())
  print('Created collections in db ', db.db_name)

"""
INSERT HERE DEFAULT CONFIGS
- Default user
- Default operation and parameters
- Default site
- Default queues
- ...
"""
