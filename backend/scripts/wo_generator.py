from pprint import pprint
from datetime import datetime, timedelta
import httpx
import random
import traceback

from arango import ArangoClient

db_client = ArangoClient(hosts='http://progress.localhost/_db')
db = db_client.db('PROGRESS_TEST', username='root', password='')
wos = db.collection('WorkOrder')
jobs = db.collection('Job')


httpx_params = {
    proxies={ "all://progress.localhost": "http://localhost:80" },
    base_url='http://progress.localhost/api/'
}

def generate_random_wos(
    quantity: int, 
    start_number: int = 220137, 
    prefix: str = 'WO', 
    max_no_lines: int = 5,
    min_wo_quantity: int = 5,
    max_wo_quantity: int = 5,
    min_due_days: int = 7,
    max_due_days: int = 300,
    set_progress: bool = True
    ) -> None:

    with httpx.Client(**httpx_params) as client:
        try:
            product_list = client.get('product').json()
            product_keys_list = [p['_key'] for p in product_list]

            wo_lines = random.randrange(5)

            # Generate 200 work orders starting from number 1032
            count = 0
            while count < quantity:
                wo_code = prefix + str(start_number + count)

                for l in range(random.randrange(max_no_lines)):
                    # select product
                    product_key = random.choice(product_keys_list)
                    # select quantity
                    qt = random.randrange(min_wo_quantity, max_wo_quantity)
                    # select due date with minimum 7 days ahead
                    due_date = datetime.now() + timedelta(random.randrange(min_due_days, max_due_days))

                    wo_data = dict(
                        wo_code=wo_code,
                        wo_line=l+1,
                        product_key=product_key,
                        qt_planned=qt,
                        due_by=due_date.isoformat()
                    )
                    r = client.post('work-order', json=wo_data)
                    print(f"Created {wo_code}")
                    count += 1
                    
            # Assign jobs when not already assigned, leaving some unassigned
            operators = [o['_key'] for o in db.collection('User').all() if 'operator' in o['scope']]
            operators_choice = operators.append(None)

            for j in [j['_key'] for j in jobs.all() if j['assigned_to'] is not None]:
                job_update = dict(
                    action='update', 
                    data=dict(
                        _key=j, 
                        assigned_to=random.choice(operators_choice)
                    )
                )
                client.post('job/update', json=job_update)

            # Set jobs progress
            

        except:
            print(traceback.format_exc())



        # select no. of lines in wo



# Assign Jobs
def assign_jobs():
    


def set_progress():




# Advance jobs





x = False
if x:
    for wo in work_orders:
        try:
            resp = r.post(url, json=wo, timeout=0.5).json()
        except:
            print(traceback.format_exc())

    # Set job completed/released quantity & overall progress
    db.aql.execute("""
        FOR j IN Job

            LET zero_or_progress = [
                0,
                CEIL(RAND()*100)
            ]

            LET progress = FLOOR(zero_or_progress[CEIL(RAND()-0.6)])

            LET qc = CEIL(j.qt_planned * progress / 100)
            LET qr_rand = RAND()*2-0.6
            LET qr = qr_rand < 0 ? 0 : MIN([ROUND(qc * qr_rand), qc])

            LET critical = RAND()-0.93 > 0
            LET on_time = RAND()-0.05 > 0
            LET active = progress ? RAND()-0.1 > 0 : RAND()-0.95 > 0

            UPDATE j WITH {
                qt_completed: qc,
                qt_released: qr,
                progress: progress,
                critical: critical,
                on_time: on_time,
                active: active
            } in Job
    """)

    # Set wo completed quantity & progress
    db.aql.execute("""
     FOR w IN WorkOrder

        LET zero_or_progress = [
                0,
                CEIL(RAND()*100)
            ]

        LET progress = FLOOR(zero_or_progress[CEIL(RAND()-0.6)])
        LET qc = FLOOR(w.qt_planned * progress * RAND() / 100)
        LET critical = RAND()-0.95 > 0
        LET on_time = RAND()-0.1 > 0
        LET active = RAND()-0.7 > 0

        UPDATE w WITH {
            progress: progress,
            qt_completed: qc,
            active: active,
            on_time: on_time,
            critical: critical
        } in WorkOrder
    """)


