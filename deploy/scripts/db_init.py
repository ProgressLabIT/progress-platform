import os
import time

from arango import ArangoClient
from passlib.context import CryptContext


# ————————————————————————————
# Setup DB
# ————————————————————————————

def get_secret(name):
  with open(f'/run/secrets/{name}') as secret:
    return secret.read().rstrip('\n')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

client = ArangoClient(hosts='http://db:8529')
root_creds = dict(username='root', password=os.getenv('DB_ROOT_PWD'))
sys_db_connection = client.db(**root_creds)

print('Checking DB status...')

db_ready = False
while not db_ready:
  try:
    log = sys_db_connection.read_log()['text']
    if 'Have fun!' in ''.join(log):
      db_ready = True
  except:
    time.sleep(0.5)

print('Database ready. Creating DB users...')
with sys_db_connection.begin_batch_execution() as sys_db:

  # ————————————————————————————
  # Create DB Users
  # ————————————————————————————
  db_users = {
    'progress_admin': get_secret('progress_admin_pwd'),
    'progress_api': get_secret('progress_api_db_pwd'),
    'customer':'customer'
  }

  # TODO: Check if users are present
  for u, pwd in db_users.items():
    sys_db.create_user(username=u, password=pwd)
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
  sys_db.update_permission(username='progress_admin', permission='rw', database='*')
  sys_db.update_permission(username='progress_api', permission='rw', database='*')
  sys_db.update_permission(username='customer', permission='ro', database='*')

  print('Done\n\nCreating collections...', end=' ')


# ————————————————————————————
# Create Collections and base records
# ————————————————————————————
collections = [
  'Batch',
  'Config',
  'Counter',
  'CustomField',
  'CustomListValue',
  'Department',
  'Event',
  'Issue',
  'IssueType',
  'issue_rel',
  'Job',
  'message',
  'Media',
  'media_connection',
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
  'wip',
  'WorkOrder',
  'WorkSession'
]

customer_admin = {
  'collection': 'User',
  'data': dict(
    username = 'cadmin',
    name = 'Utente',
    surname = 'Amministratore',
    active = True,
    psw_hash = pwd_context.hash('resetme'),
    scope = 'admin production library operator',
    site_key = '0',
    reset_password = True
  )
}

default_phase_parameters = {
  'collection': 'Config',
  'data': dict(
    _key = 'default_phase_parameters',
    parallel_job_allowed = True,
    step_check = False,
    step_check_force_order = False,
    production_batch_qt = 1,
    max_offline = 300 # 5 minutes
  )
}

site_queue = {
  'collection': 'Queue',
  'data': dict (
    type = 's',
    site_key = '0',
    work_orders = []
  )
}


db_handles = [client.db(database, **root_creds) for database in dbs]

for dbh in db_handles:
  with dbh.begin_batch_execution(return_result=True) as batch:
    for c in collections:
      # if collection name starts with a lowercase letter it's an edge collection
      batch.create_collection(name=c, edge=c[0].islower())

    for record in [customer_admin, default_phase_parameters, site_queue]:
      batch.collection(record['collection']).insert(record['data'])

    print('Created collections and data in db ', dbh.db_name)


"""
- Default user
- Default operation and parameters
- Default site
- Default queues
- ...
"""
