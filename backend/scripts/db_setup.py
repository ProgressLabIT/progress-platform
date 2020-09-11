from arango import ArangoClient
from pydantic import BaseModel

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('PROGRESS_TEST', username='root', password='')

# Collections
# https://python-driver-for-arangodb.readthedocs.io/en/master/specs.html#arango.database.TransactionDatabase.create_collection
collection_names = [
	'Batch',
	'BatchTimeRecord',
	'Department',
	'Event',
	'Job',
	'Operation',
	'Phase',
	'Product',
	'ProductionItem',
	'requires',
	'Step',
	'StepExecutionData',
	'Token',
	'User',
	'UserSession',
	'WorkOrder',
	'WorkSession'
]


# Indexes
	

# Users