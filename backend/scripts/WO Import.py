from pprint import pprint
import requests as r
import traceback


from arango import ArangoClient
client = ArangoClient(hosts='http://localhost:8529')
db = client.db('PROGRESS_TEST', username='root', password='')
wos = db.collection('WorkOrder')
jobs = db.collection('Job')


work_orders = [
  {"wo_code":"W001809","wo_line_no": 1,"product_id":"Product/11951636","qt_planned":1, "customer_data": {"po_code": "20-003245", "order_code": "OV000698", "customer_id": "Lorem S.p.A."}},
  {"wo_code":"W001810","wo_line_no": 1,"product_id":"Product/11951636","qt_planned":1, "customer_data": {"po_code": "D12-20-A00324", "order_code": "OV000701", "customer_id": "Ipsum S.r.l."}},
  {"wo_code":"W001811","wo_line_no": 1,"product_id":"Product/11954183","qt_planned":1, "customer_data": {"po_code": "00077236", "order_code": "OV000709", "customer_id": "SmallBiz Ltd"}},
  {"wo_code":"W001812","wo_line_no": 1,"product_id":"Product/11957041","qt_planned":2, "customer_data": {"po_code": "PO-20200301-3", "order_code": "OV000712", "customer_id": "ACME Inc."}},
  {"wo_code":"W001812","wo_line_no": 2,"product_id":"Product/11957378","qt_planned":1, "customer_data": {"po_code": "PO-20200301-3", "order_code": "OV000712", "customer_id": "ACME Inc."}},
  {"wo_code":"W001812","wo_line_no": 3,"product_id":"Product/11964278","qt_planned":1, "customer_data": {"po_code": "PO-20200301-3", "order_code": "OV000712", "customer_id": "ACME Inc."}},
  {"wo_code":"W001813","wo_line_no": 1,"product_id":"Product/11964421","qt_planned":20},
  {"wo_code":"W001813","wo_line_no": 2,"product_id":"Product/11964394","qt_planned":50},
  {"wo_code":"W001814","wo_line_no": 1,"product_id":"Product/11964278","qt_planned":5},
  {"wo_code":"W001815","wo_line_no": 1,"product_id":"Product/11957041","qt_planned":3, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Big Corp."}},
  {"wo_code":"W001815","wo_line_no": 2,"product_id":"Product/11992516","qt_planned":3, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Big Corp."}},
  {"wo_code":"W001815","wo_line_no": 3,"product_id":"Product/11957378","qt_planned":2, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Big Corp."}},
  {"wo_code":"W001815","wo_line_no": 4,"product_id":"Product/11964278","qt_planned":1, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Big Corp."}},
  {"wo_code":"W001816","wo_line_no": 1,"product_id":"Product/11957041","qt_planned":1, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "YourRandomEMS"}},
  {"wo_code":"W001817","wo_line_no": 2,"product_id":"Product/11957378","qt_planned":2, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "YourRandomEMS"}},
  {"wo_code":"W001818","wo_line_no": 1,"product_id":"Product/11951636","qt_planned":5, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Super Co."}},
  {"wo_code":"W001819","wo_line_no": 1,"product_id":"Product/11954183","qt_planned":3, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Super Co."}},
  {"wo_code":"W001819","wo_line_no": 2,"product_id":"Product/11992369","qt_planned":5, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Super Co."}},
  {"wo_code":"W001819","wo_line_no": 3,"product_id":"Product/11992494","qt_planned":3, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Super Co."}},
  {"wo_code":"W001819","wo_line_no": 4,"product_id":"Product/11957378","qt_planned":5, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Super Co."}},
  {"wo_code":"W001819","wo_line_no": 5,"product_id":"Product/11964278","qt_planned":3, "customer_data": {"po_code": "8002765-A76", "order_code": "OV000718", "customer_id": "Super Co."}},
  {"wo_code":"W001820","wo_line_no": 1,"product_id":"Product/11964062","qt_planned":10},
  {"wo_code":"W001820","wo_line_no": 2,"product_id":"Product/11964186","qt_planned":10},
  {"wo_code":"W001821","wo_line_no": 1,"product_id":"Product/11964062","qt_planned":10},
  {"wo_code":"W001821","wo_line_no": 2,"product_id":"Product/11964186","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 1,"product_id":"Product/11964115","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 2,"product_id":"Product/11964115","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 3,"product_id":"Product/11964159","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 4,"product_id":"Product/11964159","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 5,"product_id":"Product/11957578","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 6,"product_id":"Product/11957578","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 7,"product_id":"Product/11963904","qt_planned":10},
  {"wo_code":"W001822","wo_line_no": 8,"product_id":"Product/11963904","qt_planned":10},
]

url = "http://localhost:8000/work-order"

jobs.truncate()
wos.truncate()

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

