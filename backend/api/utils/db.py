import json

from arango import ArangoClient
from fastapi.encoders import jsonable_encoder

def model_to_db_dict(pydantic_model):
  prepped_data = jsonable_encoder(pydantic_model, by_alias=True)

  # remove null _id / _key fields
  for field in ['_id', '_key']:
    if field in prepped_data:
      if prepped_data[field] == None:
        del prepped_data[field]

  return prepped_data


def encoder(data):
  dict = model_to_db_dict(data)
  return json.dumps(dict)


client = ArangoClient(hosts='http://localhost:8529', serializer=encoder)
db = client.db('PROGRESS_TEST', username='root', password='')

