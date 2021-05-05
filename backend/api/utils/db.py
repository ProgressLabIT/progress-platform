import json

from arango import ArangoClient
from fastapi.encoders import jsonable_encoder

from utils import config


def model_to_db_dict(pydantic_model):
  prepped_data = jsonable_encoder(pydantic_model, by_alias=True)

  # remove null _id / _key fields
  for field in ['_id', '_key']:
    if field in prepped_data:
      if prepped_data[field] is None:
        del prepped_data[field]

  return prepped_data


def encoder(data):
  dict = model_to_db_dict(data)
  return json.dumps(dict)


conf = config.get_config()

client = ArangoClient(hosts=conf.arango_url, serializer=encoder)

# Get password from docker secrets or set as empty if none is present
try:
  with open(conf.api_db_pwd_file, 'r') as f:
    db_pwd = f.read()
except:
  db_pwd=''


db = client.db(conf.db_name, username=conf.api_db_username, password=db_pwd)
