import json

from arango import ArangoClient
from fastapi.encoders import jsonable_encoder

def encoder(data):
  prepped_data = jsonable_encoder(data)

  # remove null _id / _key fields
  for field in ['_id', '_key']:
    if field in prepped_data:
      if prepped_data[field] == None:
        del prepped_data[field]

  return json.dumps(prepped_data)

client = ArangoClient(hosts='http://localhost:8529', serializer=encoder)



db = client.db('PROGRESS_TEST', username='root', password='')

