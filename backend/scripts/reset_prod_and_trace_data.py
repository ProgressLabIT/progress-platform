from arango import ArangoClient

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('PROGRESS_TEST', username='root', password='')

collections = [
	'WorkSession',
	'Event',
	'StepExecutionData',
	'BatchTimeRecord',
	'Batch',
	'Job',
	'WorkOrder'
]

tx = db.begin_transaction(write=collections + ['Queue'])

for c in collections:
	tx.collection(c).truncate()

tx.collection('Queue').update_match({'site_key':'0'}, {'jobs': [], 'work_orders': []})

tx.commit_transaction()
