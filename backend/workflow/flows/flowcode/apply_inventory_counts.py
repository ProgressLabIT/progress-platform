import httpx
import os
import traceback

from prefect import task, flow
from prefect.blocks.system import Secret
from prefect.states import Failed

from utils import connect_to_progress_db


base_url=os.getenv('PROGRESS_API_URL', 'http://api:8000')
progress_api_token = Secret.load('progress-api-token').get()
headers=dict(Authorization=f'Bearer {progress_api_token}')

@task
def fetch_data_for_processing(session_key: str) -> tuple[list[dict], str]:
  """Fetch all count records in CONFIRMED status that haven't been processed yet."""
  db = connect_to_progress_db()

  # only one record per product/position pair is allowed, duplicate ones are discarded by the COUNT_SESSION_CONFIRMED event
  query = """
    FOR r IN inventory_count_record
    FILTER r.inventory_count_session_key == @session_key
      AND r.status == 'confirmed' AND r.processed != true
    RETURN MERGE(r, { product_code: DOCUMENT(r._from).code, position_code: DOCUMENT(r._to).code })
  """
  records = list(db.aql.execute(query, bind_vars={'session_key': session_key}))

  if len(records) == 0:
    raise ValueError(f"No records or movement list key found for session {session_key}")

  movement_list_key = db.collection('InventoryCountSession').get(session_key).get('adjustment_list_key')

  if movement_list_key is None:
    raise ValueError(f"No records or movement list key found for session {session_key}")

  return records, movement_list_key


def get_task_run_name(parameters: dict) -> str:
  record = parameters.get('record')
  return f"{record.get('position_code')} > {record.get('product_code')} ({record.get('_key')})"


def mark_record_failed(record: dict, error_details: str):
  db = connect_to_progress_db()
  db.collection('inventory_count_record').update(dict(
    _key=record['_key'],
    error_details=error_details
  ))


@task(task_run_name=get_task_run_name)
def apply_count_record(record: dict, session_key: str, movement_list_key: str) -> bool:
  """Apply a single count record via event API."""
  event_data = dict(
    event_type='COUNT_APPLIED',
    count_record_key=record['_key'],
    movement_list_key=movement_list_key,
    inventory_count_session_key=session_key
  )

  try:
    r = httpx.post(base_url+'/event', headers=headers, json=event_data, timeout=5)
    r.raise_for_status()
    print(f"Count record {record['_key']} applied successfully")
    return True
  except httpx.HTTPStatusError as e:
    mark_record_failed(record, r.json())
    return Failed(message=f"Error applying count record {record['_key']}. Response: \n{r.json()}")
  except Exception as e:
    mark_record_failed(record, str(e))
    return Failed(message=f"Error applying count record {record['_key']}: {traceback.format_exc()}")


@task
def finalize_session(session_key: str) -> dict:
  """Finalize the count session via event API."""
  event_data = dict(
    event_type='COUNT_SESSION_APPLIED',
    session_key=session_key
  )
  try:
    r = httpx.post(base_url+'/event', headers=headers, json=event_data, timeout=5)
    r.raise_for_status()
    print(f"Count session {session_key} finalized successfully")
  except httpx.HTTPStatusError as e:
    return Failed(message=f"Error finalizing count session {session_key}. Response: \n{r.json()}")
  except Exception as e:
    return Failed(message=f"Error finalizing count session {session_key}: {traceback.format_exc()}")

@flow(name="Apply Inventory Counts", log_prints=True)
def main(session_key: str):
  records, movement_list_key = fetch_data_for_processing(session_key)

  for record in records:
    apply_count_record(record=record, session_key=session_key, movement_list_key=movement_list_key)

  finalize_session(session_key)
