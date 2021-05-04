import secrets
import subprocess
import traceback

import docker as d
from arango import ArangoClient


# Connect to docker daemon
print('Connecting to docker daemon...', end=" ")
docker = d.from_env()
print('Done\n')

# ————————————————————————————————
# Create volumes
# ————————————————————————————————
print('Creating volumes...')
volumes_params = [
  {
    'name': 'db_data',
  },
  {
    'name': 'db_backup',
    'driver': 'local',
    'driver_opts': dict(o='bind', type='none', device='/opt/progress/db_backup')
  },
  {
    'name': 'media',
    'driver': 'local',
    'driver_opts': dict(o='bind', type='none', device='/opt/progress/media')
  },
  {
    'name': 'logs',
    'driver': 'local',
    'driver_opts': dict(o='bind', type='none', device='/opt/progress/logs')
  },
]

volumes = {}
for v in volumes_params:
  volumes[v['name']] = docker.volumes.create(**v)
  print('Created volume ', v['name'])

print('Done\n')



# ————————————————————————————
# Setup DB
# ————————————————————————————
# root_password = secrets.token_urlsafe(8)
root_password = '1234'
# Run a disposable container to bootstrap the db_data volume
print('Starting DB container....', end=' ')
db_container = docker.containers.run(
  'arangodb:3.7',
  detach=True,
  ports={8529:8529},
  remove=True,
  volumes={'db_data': dict(bind='/var/lib/arangodb3', mode='rw')},
  environment={'ARANGO_ROOT_PASSWORD': root_password}
)
print('Done\n\nCreating DB users...')

try:
  client = ArangoClient(hosts='http://localhost:8529')
  sys_db = client.db(username='root', password=root_password)

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

  db_handles = [client.db(db, username='root', password=root_password) for db in dbs]

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



  print('Done\n\n Stopping and removing container...', end=' ')

# Clean up half baked db data if something goes wrong
except Exception as e:
  print('There was an error. Removing partial data...')
  for k, v in volumes.items():
    v.remove()
  print("Done.\n\nHere's the error trace:\n\n", traceback.format_exc())

finally:
  # Close container
  print('Stopping and removing DB container...', end=" ")
  db_container.stop()
  print('Done\n\n')

# ————————————————————————————
# Create app users
# ————————————————————————————

print('Initializing Swarm...')
# Init Swarm - required to save secrets
docker.swarm.init()
join_token_manager = subprocess.run('docker swarm join-token -q manager', shell=True, capture_output=True)

# Save db password in docker secrets
print('Encrypting passwords in a secure environment...', end=' ')
for username, pwd in users.items():
  docker.secrets.create(name=f'db_pwd_{username}', data=pwd)
print('Done')

print("Join swarm as a manger with the following token:\n\n", join_token_manager.stdout)
# subprocess run returns a CompletedProcess object, and the stdout is a b'' and includes a \n at the end, to be removed.

# ————————————————————————————
# Deploy stack
# ————————————————————————————
# Login, making sure to fail gracefully and warn the user if it fails
# try:
#   docker.login(
#     registry='registry.gitlab.com',
#     username='installations@progresslab.it',
#     password='YkKxdqb9zwdz6svzt92a' # full api access until 31/12/2021
#   )
# except docker.errors.APIError:
#   print('Could not login to registry. Please contact your account reference')

# class ProgressDBAdmin:

#   def __init__(self, docker_client, db_url):
#     self.docker = docker_client
#     self.db_client = ArangoClient(hosts=db_url)
#     self.sys_db = self.db_client.db(username='root', password='')


#   # ————————————————————————————
#   # Users
#   # ————————————————————————————
#   def db_pwd_gen(username: str) -> str:
#     # create a random password and store it as a docker secrets
#     pwd = secrets.token_urlsafe()
#     # docker.secrets...
#     return pwd

#   def create_users(users: List[str]) -> None:
#     for u in users:
#       sys_db.create_user(username=u, password=db_pwd_gen(u))

#   # ————————————————————————————
#   # create DBs
#   # ————————————————————————————
#   def create_dbs(db_list: List[str]) -> None:
#     for db in db_list:
#       sys_db.create_database(db)
