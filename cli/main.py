import random
import traceback

import typer
import httpx

from datetime import datetime, timedelta

from arango import ArangoClient
from pprint import pprint


app = typer.Typer()

db_client = ArangoClient(hosts='http://db:8529')
db = db_client.db('PROGRESS_TEST', username='root', password='')
wos = db.collection('WorkOrder')
jobs = db.collection('Job')


httpx_params = dict(
    proxies={ "all://progress.localhost": "http://localhost:80" },
    base_url='http://progress.localhost/api'
)

@app.command()
def reset_production_and_traceability_data() -> None:
  collections = [
    'Batch',
    'Event',
    'Job',
    'Queue',
    'StepExecutionData',
    'WIP',
    'WorkOrder',
    'WorkSession',
  ]

  tx = db.begin_transaction(write=collections)

  for c in collections:
    tx.collection(c).truncate()

  tx.collection('Queue').insert(dict(
    type = 's', #What the queue refers to.
    site_key = '0',
    subqueue_target_key = None,
    work_orders = [],
    jobs = []
  ))

  tx.commit_transaction()

@app.command()
def generate_random_wos(
    quantity: int = 10,
    start_number: int = 220137,
    prefix: str = 'WO',
    max_no_lines: int = 5,
    min_wo_quantity: int = 5,
    max_wo_quantity: int = 20,
    min_due_days: int = 7,
    max_due_days: int = 300,
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
            user_list = client.get('user').json()['detail']
            operators = [o['_key'] for o in user_list if 'operator' in o['scope']]
            operators.append(None)

            job_list = client.get('job').json()['detail']
            jobs_to_assign = [job['_key'] for job in job_list if job['assigned_to'] is None]

            job_updates = []
            for j in jobs_to_assign:
              assignee = random.choice(operators)
              update = dict(
                action='update',
                data=dict(
                  _key=j,
                  assigned_to=assignee
                )
              )
              job_updates.append(update)

            r = client.post('job/update', json=job_updates)

        except:
            print(traceback.format_exc())

@app.command()
def set_progress() -> None:
  job_progress_query = """
    FOR j IN Job
    FILTER j.assigned_to

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
  """

  wo_progress_query = """
    LET now = DATE_NOW()

    FOR wo IN WorkOrder
    FILTER wo._key == @wo_key
    LET jobs = (FOR j IN Job FILTER j.wo_key == @wo_key RETURN j)

    // Update progress
    LET progress = ROUND(AVERAGE(
      FOR phase IN wo.phase_sequence
      RETURN SUM(
        FOR j IN jobs
        FILTER j.phase_key == phase
        RETURN j.progress * j.qt_planned
      ) / wo.qt_planned
    ))

    // Update active state
    LET active = TO_BOOL(SUM(
      FOR j IN jobs
      FILTER j.active
      RETURN 1
    ))

    // Update completed quantity
    LET qt_completed = SUM(
      FOR j IN jobs
      FILTER j.phase_key == LAST(wo.phase_sequence)
      RETURN j.qt_released
    )

    // Update PT and Cost
    LET processing_time = SUM(
      FOR ws IN WorkSession
      FILTER ws.work_order_key == @wo_key
      RETURN ws.duration
    )

    LET processing_cost = SUM(
      FOR ws IN WorkSession
      FILTER ws.work_order_key == @wo_key
      RETURN CEIL(ws.duration / (60*60*1000)) * ws.hourly_cost
    )

    // Check if any WO Job is still open
    LET still_open = TO_BOOL(COUNT(FOR j IN jobs FILTER j.stage != 'closed' RETURN 1))
    LET status = still_open ? 'started' : 'closed'

    LET end = still_open ? null : DATE_ISO8601(now)

    // Verify if WO is critical
    LET critical = TO_BOOL(COUNT(FOR j IN jobs FILTER j.critical RETURN 1)))


    // Apply changes and return updated record
    UPDATE wo WITH {

      progress,
      active,
      qt_completed,
      status,
      end,
      processing_time,
      processing_cost,
      critical

    } IN WorkOrder RETURN NEW
  """

  tx = db.begin_transaction(write=["Job", "WorkOrder"])
  # Set job completed/released quantity & overall progress
  tx.aql.execute(job_progress_query)
  # Set wo completed quantity & progress
  tx.aql.execute(wo_progress_query)
  # Commit changes
  tx.commit_transaction()



if __name__ == '__main__':
  app()
