from arango import ArangoClient

DB_NAME = 'PROGRESS_TEST'  # change to your demo DB name
client = ArangoClient(hosts='http://db:8529')
db = client.db(DB_NAME, username='root', password='')

# D1: 2-level (depot → aisle → shelf)
D1_AISLES = ['A', 'B', 'C', 'D']
D1_SHELVES_PER_AISLE = 12

# D2: 3-level ikea-style (depot → aisle → shelf → bin), 4×5×10 = 200 bins
D2_AISLES = ['A', 'B', 'C', 'D']
D2_SHELVES_PER_AISLE = 5
D2_BINS_PER_SHELF = 10

tx = db.begin_transaction(write=['Position', 'is_in_position'])
positions = tx.collection('Position')
edges = tx.collection('is_in_position')


def add(code, parent_key):
    doc = positions.insert(
        {
            'code': code,
            'owned': True,
            'available': True,
            'disposable': False,
            'fixed': True,
            'deleted': False,
        },
        return_new=True,
    )
    key = doc['_key']
    edges.insert({'_from': f'Position/{key}', '_to': f'Position/{parent_key}'})
    return key


# D1: depot → aisle (A–D) → shelf (01–12)
d1 = add('D1', 'IN')
for a in D1_AISLES:
    aisle = add(f'D1-{a}', d1)
    for s in range(1, D1_SHELVES_PER_AISLE + 1):
        add(f'D1-{a}-{s:02d}', aisle)

# D2: depot → aisle (A–D) → shelf (1–5) → bin (01–10)
d2 = add('D2', 'IN')
for a in D2_AISLES:
    aisle = add(f'D2-{a}', d2)
    for s in range(1, D2_SHELVES_PER_AISLE + 1):
        shelf = add(f'D2-{a}-{s}', aisle)
        for b in range(1, D2_BINS_PER_SHELF + 1):
            add(f'D2-{a}-{s}-{b:02d}', shelf)

tx.commit_transaction()
print('Done. Seeded 278 positions:')
print(f'  D1: 1 depot + {len(D1_AISLES)} aisles + {len(D1_AISLES) * D1_SHELVES_PER_AISLE} shelves = 53')
print(
    f'  D2: 1 depot + {len(D2_AISLES)} aisles'
    f' + {len(D2_AISLES) * D2_SHELVES_PER_AISLE} shelves'
    f' + {len(D2_AISLES) * D2_SHELVES_PER_AISLE * D2_BINS_PER_SHELF} bins = 225'
)
