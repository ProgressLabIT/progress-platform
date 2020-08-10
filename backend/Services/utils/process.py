import os
from utils.db import db
from utils.file import UserFile

def search_step_media(step_key: str):

  step_media = UserFile.step_media(step_key)
  media_folder_exists = os.path.isdir(step_media.folder_path)

  if (media_folder_exists):
    return step_media.get_folder_contents()

  else:
    return []



def get_products_using_operation(op_key):
  cursor = db.aql.execute("""
      FOR v IN 2..2 INBOUND CONCAT('Operation/', @op_key) requires
      FILTER PARSE_IDENTIFIER(v._id).collection == 'Product'
      RETURN KEEP(v, 'code', '_key')
    """, bind_vars=dict(op_key=op_key))

  return [product for product in cursor]