import os
from os import path

from utils.db import db
from utils.config import get_config

media_root_path = get_config().media_path

def get_media_path(media_key: str):
  return path.join(media_root_path, media_key)

def delete_media(media_key: str):
  """
  Delete the media from the disk and the database.
  It does not perform checks to ensure that the media is not connected to any entity.
  So, it should only be called when it is known that the media is not connected to any entity.
  """

  # Using a transaction to ensure that the media is deleted from both the disk and the database.
  tx = db.begin_transaction(write=['Media'])

  try:
    deleted_media = db.collection('Media').delete(media_key, return_old=True)['old']
  except:
    tx.abort_transaction()
    raise Exception('Could not delete media from database')

  try:
    filepath = path.join(media_root_path, media_key)
    os.remove(filepath)
  except:
    tx.abort_transaction()
    raise Exception('Could not delete file from disk')

  tx.commit_transaction()
  return deleted_media
