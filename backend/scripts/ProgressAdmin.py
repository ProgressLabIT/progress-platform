import secrets, os

import docker

from db_setup import setup_db

class ProgressAdmin:

  volumes_params = [
    {
      'name': 'db_data',
    }
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

  registry_username = 'installations@progresslab.it'

  collections = [
    'Batch',
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

  dbs = [
    'PROGRESS_DEV',
    'PROGRESS_TEST',
    'PROGRESS_PROD'
  ]

  users = [
    'progress_dev',
    'progress_api',
    'customer'
  ]

  def __init__(self):
    # Connect to docker daemon
    self.d = docker.from_env()


  def log_into_registry(self, token_file_path: str) -> None:
    pass


  def create_volumes(self) -> None:
    # TODO Check existence of volumes

    # Create volumes
    for v in volumes_params:
      self.volumes[v.name] = self.d.volumes.create(**v)


  def setup_db(self) -> None:
    # Run a disposable container to bootstrap the db_data volume
    docker.containers.run(
      'arangodb:3.7',
      detach=True,
      ports={8529:8529},
      remove=True,
      volumes={'db_data': '/var/lib/arangodb3'}
    )

    setup_db()


  def
