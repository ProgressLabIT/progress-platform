from fastapi import APIRouter, UploadFile
from shutil import copyfileobj
from os import path, remove, makedirs

from utils.api import APIResponse
from utils.media import media_root_path
from utils.db import db
from utils.exceptions import HTTPError

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

@router.patch('/config')
def update_config(config: dict):
  try:
    to_insert = []
    to_update = []
    for key, value in config.items():
      if value is None:
        continue

      target = to_update if db.collection('Config').has(key) else to_insert

      if isinstance(value, dict):
        target.append(dict(_key=key, **value))
      else:
        target.append(dict(_key=key, value=value))

    if to_insert:
      db.collection('Config').insert_many(to_insert)
    if to_update:
      db.collection('Config').update_many(to_update)

    return APIResponse(
      message = "Config updated successfully",
    )
  except:
    raise HTTPError(500, "Failed to update config")

@router.put('/config/{key}/file')
def update_config_file(key: str, file: UploadFile):
  try:
    config = db.collection('Config').get(key)
    if not config:
      config = db.collection('Config').insert(dict(_key=key, value=""))

    # Remove the old file if it exists
    if path.exists(config['value']):
      remove(config['value'])

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
