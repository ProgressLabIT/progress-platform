from fastapi import APIRouter, UploadFile, Depends
from shutil import copyfileobj
from os import path, remove, makedirs

from utils.api import APIResponse
from utils.media import media_root_path
from utils.db import db
from utils.exceptions import HTTPError
from utils.production import Queries as ProductionQueries
from utils import auth


router = APIRouter()

@router.get('/config')
def get_config():
  try:
    configurations = db.collection('Config').all()
    result = dict()
    for configuration in configurations:
      key = configuration['_key']
      config = { k: v for k, v in configuration.items() if k not in ['_key', '_id', '_rev'] }
      result[key] = config['value'] if 'value' in config and len(config.keys()) == 1 else config

    return APIResponse(
      message = "Config retrieved successfully",
      detail = result
    )
  except:
    raise HTTPError(500, "Failed to retrieve config")

@router.patch('/config',
    dependencies=[Depends(auth.verify_token)])
def update_config(config: dict):

  default_values = {
    'default_production_position': 'IN',
    'default_consumption_position': 'IN'
  }

  try:
    tx = db.begin_transaction(write=['Config', 'Queue'])

    to_insert = []
    to_update = []
    for key, value in config.items():
      if value is None:
        if not key in default_values:
          continue
        else:
          value = default_values[key]

      target = to_update if db.collection('Config').has(key) else to_insert

      if isinstance(value, dict):
        target.append(dict(_key=key, **value))
      else:
        target.append(dict(_key=key, value=value))

      # If turning off the feature, we should update the queues and reorder them as usual to avoid any hidden behavioral changes
      if key == 'allow_independent_reordering_of_job_queues' and value == False:
        updated_operators_cursor = tx.aql.execute(
          """
          FOR queue IN Queue
            FILTER queue.type == 'o' && queue.independent == true
            UPDATE queue WITH { independent: false } IN Queue
            RETURN NEW.subqueue_target_key
          """
        )
        updated_operators = list(updated_operators_cursor)
        if not updated_operators:
          continue

        tx.aql.execute(
          ProductionQueries.REORDER_JOB_QUEUES,
          bind_vars=dict(
            # TODO: re-order job queues in all sites when site management is implemented. None will default to '0' in the query
            site_key = None,
            target_key = updated_operators,
          )
        )

    if to_insert:
      tx.collection('Config').insert_many(to_insert)
    if to_update:
      tx.collection('Config').update_many(to_update)

    tx.commit_transaction()

    return APIResponse(
      message = "Config updated successfully",
    )
  except:
    tx.abort_transaction()
    raise HTTPError(500, "Failed to update config")

@router.put('/config/{key}/file',
    dependencies=[Depends(auth.verify_token)])
def update_config_file(key: str, file: UploadFile | None = None):
  try:
    config = db.collection('Config').get(key)
    if not config:
      config = db.collection('Config').insert(dict(_key=key, value=""))

    # Remove the old file if it exists
    if config['value'] is not None and path.exists(config['value']):
      remove(config['value'])

    if not file:
      db.collection('Config').update(dict(_key=key, value=None))
      return APIResponse(
        message = "File for config parameter updated successfully",
        detail = dict(file_path=None)
      )

    folder_path = path.join(media_root_path, 'config', key)
    if not path.exists(folder_path):
      makedirs(folder_path)

    file_path = path.join(folder_path, file.filename)
    with open(file_path, 'wb') as buffer:
      copyfileobj(file.file, buffer)

    db.collection('Config').update(dict(_key=key, value=file_path))

    return APIResponse(
      message = "File for config parameter updated successfully",
      detail = dict(file_path=file_path)
    )
  except:
    raise HTTPError(500, "Failed to update config file")
