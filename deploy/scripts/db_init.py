import os
import time

from arango import ArangoClient
from pydantic import BaseModel, Field
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
class DBIndex(BaseModel):
  type: str | None = 'persistent'
  fields: list[str]
  name: str
  storedValues: list[str] | None = Field(None, exclude=True)

class Collection(BaseModel):
  name: str
  indexes: list[DBIndex] | None =[]
  default_records: list[dict] | None = []


collections = [
  Collection(name='Batch',indexes=[
    DBIndex(fields=['job_key, canceled'], name='batch-job-canceled'),
    DBIndex(fields=['work_order_key, phase_key, canceled'], name='batch-wo-phase-canceled')
  ]),
  Collection(name='batch_serial'),
  Collection(name='can_use_print_template'),
  Collection(name='Config', default_records=[
    dict(
      _key = 'company_logo',
      value = None
    ),
    dict(
      _key = 'company_name',
      value = 'PROGRESS PLATFORM'
    ),
    dict(
      _key = 'default_operation_parameters',
      parallel_job_allowed = True,
      display_job_timer = False,
      step_check = False,
      step_check_force_order = False,
      production_batch_qt = 1,
      max_offline = 300, # 5 minutes
      std_processing_time = 60 # 1 minute
    ),
    dict(
      _key = 'show_unassigned_jobs_to_operators',
      value = True
    ),
    dict(
      _key = 'allow_independent_reordering_of_job_queues',
      value = False
    ),
    dict(
      _key = 'allow_serial_delete',
      value = True
    ),
    dict(
      _key = 'enable_inventory_management',
      value = False
    ),
    dict(
      _key = 'default_production_position',
      value = 'IN'
    ),
    dict(
      _key = 'default_consumption_position',
      value = 'IN'
    ),
    dict(
      _key = 'operator_cost',
      value = 25
    ),
    dict(
      _key = 'system_counters',
      value = dict(
        work_orders = 'default',
        warehouse_missions = 'default',
        positions = 'default'
      )
    ),
  ]),
  Collection(name='contains'),
  Collection(name='Counter', default_records=[
    dict(
      _key = 'default',
      next_tick = 1,
      template = ['%y', '#6'],
      frequency = "year",
      reset_date = ""
    )
  ]),
  Collection(name='CustomField'),
  Collection(name='CustomListValue', indexes=[
    DBIndex(fields=['field_key'], name='clv-field')
  ]),
  Collection(name='Department'),
  Collection(name='Event', indexes=[
    DBIndex(fields=['issue_key'], name='event-issue'),
    DBIndex(fields=['serial_key'], name='event-serial'),
    DBIndex(fields=['timestamp'], name='event-timestamp')
  ]),
  Collection(name='has_tag'),
  Collection(name='movement', indexes=[
    DBIndex(fields=['product_key', 'status', 'stage'], name='movement-product'),
    DBIndex(fields=['serial_key'], name="movement-serial"),
    DBIndex(fields=['list_key'], name="movement-list"),
    DBIndex(fields=['start', 'end'], name="movement-time-range"),
  ]),
  Collection(name='Issue', indexes=[
    DBIndex(fields=['issue_type_key'], name="issue-type"),
    DBIndex(fields=['created'], name='issue-created-time'),
    DBIndex(fields=['open'], name='issue-open'),
    DBIndex(fields=['critical'], name='issue-critical')
  ]),
  Collection(name='issue_rel'),
  Collection(name='IssueType'),
  Collection(name='Job', indexes=[
    DBIndex(fields=['wo_key, phase_key, assigned_to, stage'], name='job-target'),
    DBIndex(fields=['assigned_to, stage'], name='job-assignment'),
    DBIndex(fields=['active'], name='job-active')
  ]),
  Collection(name='is_in_position',
    indexes=[
      DBIndex(fields=['serial_key'], name='inventory-serial')
    ],
    default_records=[
      dict(
        _key = 'IN',
        code = 'IN',
        owned = True,
        available = True,
        disposable = False,
        extra = None
      ),
      dict(
        _key = 'OUT',
        code = 'OUT',
        owned = False,
        available = False,
        disposable = False,
        extra = None
      )
    ]
  ),
  Collection(name='Media'),
  Collection(name='media_connection'),
  Collection(name='message'),
  Collection(name='Operation'),
  Collection(name='Phase', indexes=[
    DBIndex(fields=['product_key, operation_key'], name='phase-product-operation')
  ]),
  Collection(name='Position', indexes=[
    DBIndex(fields=['_key'], storedValues=['code'], name='position-key'),
    DBIndex(fields=['code'], storedValues=['_key'], name='position-code'),
    DBIndex(fields=['_key', 'code'], name='position-key-code')
  ]),
  Collection(name='PrintTemplate'),
  Collection(name='Product', indexes=[
    DBIndex(fields=['_key'], storedValues=['code'], name='product-key-code'),
    DBIndex(fields=['code'], storedValues=['_key'], name='product-code-key')
  ]),
  Collection(
    name='Queue',
    indexes=[
      DBIndex(fields=['type, independent, subqueue_target_key'], name='queue-type-independent-target'),
      DBIndex(fields=['subqueue_target_key'], name="queue-target")
    ],
    default_records=[
      dict(
        type = 's',
        site_key = '0',
        work_orders = []
      )
    ]
  ),
  Collection(name='requires'),
  Collection(name='Serial', indexes=[
    DBIndex(fields=['_key'], storedValues=['code'], name='serial-key-code'),
    DBIndex(fields=['code'], storedValues=['_key'], name='serial-code-key'),
    DBIndex(fields=['wo_key', 'released'], name='serial-wo'),
    DBIndex(fields=['product_key', 'released'], name='serial-product'),
    DBIndex(fields=['released'], name='serial-released'),
  ]),
  Collection(name='Site'),
  Collection(name='Step'),
  Collection(name='StepExecutionData', indexes=[
    DBIndex(fields=['batch_key, step_key, status, canceled'], name='sxd-batch-step-status-canceled')
  ]),
  Collection(name='Tag'),
  Collection(name='Token'),
  Collection(name='User', default_records=[
    dict(
      username = 'cadmin',
      name = 'Utente',
      surname = 'Amministratore',
      active = True,
      psw_hash = pwd_context.hash('resetme'),
      scope = 'admin production library operator',
      site_key = '0',
      reset_password = True
    )
  ]),
  Collection(name='UserSession'),
  Collection(name='wip', indexes=[
    DBIndex(fields=['wo_key'], name='wip-wo'),
    DBIndex(fields=['batch_key'], name='wip-batch'),
    DBIndex(fields=['serial_key'], name='wip-serial'),
    DBIndex(fields=['_to, wo_key, active, serial_key'], name='wip-target'),
  ]),
  Collection(name='MovementList', indexes=[
    DBIndex(fields=['code'], storedValues=['_key'], name="list-code-key"),
    DBIndex(fields=['_key'], storedValues=['code'], name="list-key-code"),
    DBIndex(fields=['status', 'assigned_to'], name="list-status-assignee")
  ]),
  Collection(name='WorkOrder', indexes=[
    DBIndex(fields=['_key'], storedValues=['code'], name='workorder-key-code'),
    DBIndex(fields=['code'], storedValues=['_key'], name='workorder-code-key')
  ]),
  Collection(name='WorkSession', indexes=[
    DBIndex(fields=['work_order_key'], name='ws-wo'),
    DBIndex(fields=['job_key, canceled'], name='ws-job-canceled'),
    DBIndex(fields=['user_key, active'], name='ws-user-active'),
    DBIndex(fields=['batch_key, canceled'], name='ws-batch-canceled'),
  ])
]


db_handles = [client.db(database, **root_creds) for database in dbs]

for db in db_handles:
  for c in collections:
    # if collection name starts with a lowercase letter it's an edge collection
    db.create_collection(name=c.name, edge=c.name[0].islower())
    collection = db.collection(c.name)

    for index in c.indexes:
      collection.add_index(index.model_dump())

    if len(c.default_records):
      collection.insert_many(c.default_records)

    print(f"Created collection {c.name} in {db.db_name}")

  print('Created collections and data in db ', db.db_name)


