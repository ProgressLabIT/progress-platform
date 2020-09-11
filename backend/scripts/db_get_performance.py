import timeit

from arango import ArangoClient

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('PROGRESS_TEST', username='root', password='')



def get_user():
  return db.collection('User').get('12005319')


trials = timeit.repeat(get_user, repeat=10, number=1000)
performance = sum(trials)/len(trials)
print(performance)