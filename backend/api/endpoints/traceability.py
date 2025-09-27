import traceback

from fastapi import APIRouter, HTTPException, Depends
from utils import auth

from models.event import EventInfoModel, EventType, EventContextType
from models.traceability import *

from utils.exceptions import *
from utils.api import APIResponse
from models.serial import SerialSelection, SerialLink
from models.form import FormFieldValue
from utils.db import db
from utils.dt import timestamp
from utils.event import get_event_class
from utils.serial import Queries as SerialQueries
from utils.traceability import Queries

router = APIRouter()

serials = db.collection('Serial')

context_map = {
  EventContextType.TASK.value: 'Task',
}


@router.post('/event',
    dependencies=[Depends(auth.verify_token)])
async def record_event(event_data: EventInfoModel):
  # Event data validation will happen at the event class level
  try:
    event_class = get_event_class(event_data.event_type)
    event = event_class(info=event_data.model_dump())

    # Validate event context
    if event.info.context_type is not None:
      if event.info.context_type not in context_map:
        raise HTTPException(status_code=422, detail=f'Invalid context type: {event.info.context_type}')
      if event.info.context_key is None:
        raise HTTPException(status_code=422, detail='Context key is required')
      context_collection = context_map[event.info.context_type]
      if not db.collection(context_collection).has(event.info.context_key):
        raise HTTPException(status_code=422, detail=f'Context {event.info.context_type} with key {event.info.context_key} not found')

    event.save()
    return APIResponse(detail=event.response)

  except (
    JobIsActiveError,
    JobHasActiveBatchError,
    JobHasNoAssigneeError,
    JobHasNoActiveBatchError,
    ValueError,
    WipNotAvailableError,
    SerialNotDeletedError,
    SerialNotUpdatedError,
    SerialNotLinkedError,
    SerialNotCreatedError,
    SerialCodeAlreadyPresent,
    InventoryMovementException
  ) as e:
    print(e)
    raise HTTPException(
      status_code=422,
      detail=dict(
        error_type = e.__class__.__name__,
        message = len(e.args) > 0 and e.args[0] or None,
        exception = traceback.format_exc()
      )
    )

  except Exception as e:
    status_code=500
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message="There was a problem saving the event in the db",
      error=error_str
    )

    raise HTTPException(
      status_code=status_code,
      detail=response
    )



@router.get('/event',
    dependencies=[Depends(auth.verify_token)])
async def get_events(
  issue_key: str | None = None,
  serial_key: str | None = None,
  job_key: str | None = None,
  work_order_key: str | None = None,
  task_key: str | None = None,
  time_from: datetime | None = None,
  time_to: datetime | None = None,
  context_type: EventContextType | None = None,
  context_key: str | None = None,
  type: EventType | None = None
):

  if context_type is not None and context_type not in context_map:
    raise HTTPException(status_code=422, detail=f'Invalid context type: {context_type}')

  bind_vars = dict(
    issue_key = issue_key,
    serial_key = serial_key,
    job_key = job_key,
    work_order_key = work_order_key,
    task_key = task_key,
    time_from = time_from,
    time_to = time_to,
    context_type = context_type,
    context_key = context_key,
    type = type
  )
  return [e for e in db.aql.execute(Queries.GET_EVENTS, bind_vars=bind_vars)]



@router.get('/batch/{batch_key}',
    dependencies=[Depends(auth.verify_token)])
async def get_batch_execution_data(batch_key: str):

  try:
    db_resp = db.aql.execute(Queries.GET_BATCH_EXECUTION_DATA, bind_vars=dict(batch_key=batch_key))
    batch_data = db_resp.next()

  except StopIteration:
    batch_data = dict()

  except Exception:
    status_code=500
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message="There was a problem retrieving the batch from the db",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  return APIResponse(detail=batch_data)

@router.get('/batch/{batch_key}/serials',
    dependencies=[Depends(auth.verify_token)])
async def get_batch_serials(batch_key: str):

  try:
    batch_serials_cursor = db.aql.execute(
      SerialQueries.GET_BATCH_SERIALS,
      bind_vars = dict(batch_key=batch_key)
    )

    batch_serials = [SerialSelection(**s) for s in batch_serials_cursor]

    for s in batch_serials:
      s.active = True

    return batch_serials

  except StopIteration:
    return HTTPException(
      status_code=404,
      detail=f"No serials found associated with batch {batch_key}"
    )

  except Exception as e:
    return HTTPException(
      status_code=500,
      detail=f"There was an error on our end: {traceback.format_exc()}"
    )


@router.post('/job/{job_key}/heartbeat',
    dependencies=[Depends(auth.verify_token)])
async def job_heartbeat(job_key: str, work_session_key: str | None = None):
  """
  Updates the work session `last_online` attribute with current time
  """
  try:
    now = timestamp()
    tx = db.begin_transaction(write=['Job', 'WorkSession'])
    tx.collection('Job').update({"_key": job_key, "last_online": now})

    """
    TODO: INSERT HERE UPDATE OF FALSELY CLOSED WORK SESSIONS

    E.g. If work_session_key exists and it's inactive, update it with active state and remove the end time
    """

    tx.commit_transaction()

    return APIResponse(detail={"last_online": now})

  except Exception:
    tx.abort_transaction()


@router.get('/wip',
    dependencies=[Depends(auth.verify_token)])
async def get_wip_availability_for_job(job_key: str):
  tx = db.begin_transaction()
  available_wip_records = tx.aql.execute(
    Queries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
    bind_vars=dict(job_key=job_key)
  ).next()

  free_wip_qt_upstream = sum(w['quantity'] for w in available_wip_records['upstream_free_wip'])
  free_wip_qt_downstream = sum(w['quantity'] for w in available_wip_records['downstream_free_wip'])

  return dict(
    job_key = job_key,
    free_wip_qt_downstream = free_wip_qt_downstream,
    free_wip_qt_upstream = free_wip_qt_upstream
  )


@router.post('/batch/temp-data', dependencies=[Depends(auth.verify_token)])
async def store_temp_step_data(data: ExecutionDataUpdate):
  """
  Creates or updates a step execution data record with the given form data
  without setting the step as done
  """
  execution_data = db.collection('StepExecutionData')

  # Ensure context is provided
  if data.execution_record_key is None and data.step_key is None:
    raise HTTPException(
      status_code=422,
      detail="Either execution_record_key or the combination of batch_key and step_key must be provided"
    )

  # Ensure form data is provided
  if len(data.form_data) == 0:
    raise HTTPException(
      status_code=422,
      detail="Form data must be provided"
    )

  # Get existing record or create a new one
  try:
    if data.execution_record_key:
      record = execution_data.get(data.execution_record_key)
    else:
      record = execution_data.find(dict(
        batch_key = data.batch_key,
        step_key = data.step_key,
        canceled = None
      )).next()

    if record['status'] == StepStatus.DONE.value:
      raise HTTPException(
        status_code=422,
        detail="Step is already marked as done, use STEP_EDITED event to update step data."
      )

    for field in record['form_data']:
      for new_field in data.form_data:
        if field['form_field_key'] == new_field.form_field_key:
          field['value'] = new_field.value
    execution_data.update(record)

  except StopIteration: # No existing record found, create a new one
    # Get form fields for the step
    form_fields = db.collection('Step').get(data.step_key)['form_fields']

    # Make sure to include all form fields, even if they are not provided in the form data
    form_data = []
    for field in form_fields:
      field_data = FormFieldValue(
        form_field_key = field['_key'],
        custom_field_key = field['custom_field_key'],
      )
      for new_field in data.form_data:
        if field['_key'] == new_field.form_field_key:
          field_data.value = new_field.value
      form_data.append(field_data)

    step_execution_data = StepExecutionData(
      batch_key = data.batch_key,
      step_key = data.step_key,
      form_data = form_data
    )
    record = execution_data.insert(step_execution_data.model_dump(by_alias=True))

  return APIResponse(message="Step data stored", detail=dict(
    execution_record_key = record['_key']
  ))



@router.put('/batch/{batch_key}/serial-temp-links', dependencies=[Depends(auth.verify_token)])
def create_temporary_link(batch_key: str, links: list[SerialLink]):
  """
  Replace batch temporary component serial links with the provided ones
  """
  # Check if batch_key is valid
  if not db.collection('Batch').has(batch_key):
    raise HTTPException(
      status_code=404,
      detail=f"Batch {batch_key} not found"
    )

  # If all links are for the batch, connect to the batch
  connect_to_batch = set(link.parent_serial_key for link in links) in [set(['components']), set([None])]

  # Check if all links are valid
  serial_keys = (set(link.parent_serial_key for link in links) | set(link.child_serial_key for link in links)) - set([None, 'components'])
  for serial_key in serial_keys:
    if not db.collection('Serial').has(serial_key):
      raise HTTPException(
        status_code=404,
        detail=f"Serial {serial_key} not found"
      )

  # Check if all links are temporary
  for link in links:
    if link.confirmed:
      raise HTTPException(
        status_code=403,
        detail="Cannot create confirmed link via this endpoint. Use SerialLinkedEvent instead."
      )
  # Check if all links are for the given batch
  for link in links:
    if link.batch_key != batch_key:
      raise HTTPException(
        status_code=403,
        detail=f"Link {link.parent_serial_key} -> {link.child_serial_key} Not related to batch {batch_key}"
      )

  # Delete all existing temporary links for these serials
  db.collection('contains').delete_match(dict(batch_key=batch_key))

  if connect_to_batch:
    for link in links:
      link.parent_serial_key = f'Batch/{batch_key}'

  # Create the new temporary links
  new_links = [link.model_dump(by_alias=True, exclude={'key'}) for link in links]
  new_link_records = db.collection('contains').insert_many(new_links)

  return APIResponse(
    message="Temporary serial links updated successfully",
  )
