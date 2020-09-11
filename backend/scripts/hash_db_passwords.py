from arango import ArangoClient
from passlib.context import CryptContext

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('PROGRESS_TEST', username='root', password='')

psw_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


users = [u for u in db.collection('User').all()]

for u in users:
	print(u)
	new_u = dict(**u, psw_hash=psw_context.hash(str(u['password'])))
	db.update_document(new_u)
	print(db.document(new_u['_id']))