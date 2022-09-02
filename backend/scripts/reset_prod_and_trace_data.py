from arango import ArangoClient

client = ArangoClient(hosts='http://db:8529')
db = client.db('PROGRESS_TEST', username='root', password='')

collections = [
	'Batch',
	'Event',
	'Job',
  'Queue',
	'Serial',
	'StepExecutionData',
	'WIP',
	'WorkOrder',
	'WorkSession',
]

tx = db.begin_transaction(write=collections)

for c in collections:
	tx.collection(c).truncate()

# tx.collection('Queue').update_match({'site_key':'0'}, {'jobs': [], 'work_orders': []})

tx.commit_transaction()
