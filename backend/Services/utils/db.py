from arango import ArangoClient
from fastapi.encoders import jsonable_encoder

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('PROGRESS_TEST', username='root', password='')

