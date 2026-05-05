import json
import logging
import traceback
from fastapi import APIRouter, HTTPException, Depends
from nats.errors import NoRespondersError
from utils import auth

from utils.nats_client import publish_sync, subtopic_to_subject
from models.print import PrintTemplateRecord, TemplateAssignmentUpdate, TemplateAssignmentUpdateType, TemplateAssignmentContext
from models.print_job import PrintJobRequest
from utils.api import APIResponse
from utils.db import db
from utils.nats_client import request as nats_request
from utils.print import preprocess_template, build_template_assignment_record

logger = logging.getLogger("print")

router = APIRouter()


# Fetch Print Templates
@router.get('/print-template',
    response_model=list,
    responses={500: {"description": "Database query error"}},
    dependencies=[Depends(auth.verify_token)])
async def find_print_templates(
  context: TemplateAssignmentContext | None = None,
  context_key: str | None = None,
):
  """List print templates, optionally scoped to a specific entity context.

  When called without parameters, returns all `PrintTemplate` documents with
  their name, description, and `entities` count (number of `can_use_print_template`
  edges pointing to each template), sorted by name.

  When `context='template'`, returns the matching template by `context_key`.

  When `context` is any other entity type (`product`, `phase`, `step`,
  `issue_type`, `task_type`, `position`), returns only templates assigned to
  the entity identified by `context_key` via `can_use_print_template` edges.

  Note: full template `basePdf` and `schemas` data are not included in list
  responses — use `GET /print-template/{template_key}` for full details.

  **Emits:** *(direct query — no event class)*

  **Required scope:** `quality:print-template:read`
  """
  if context is None:
    cursor = db.aql.execute(
      """
      FOR template IN PrintTemplate

      LET entities = (
        FOR edge IN can_use_print_template
          FILTER edge._to == template._id
          return edge
      )

      SORT template.name
      RETURN MERGE(KEEP(template, '_key', 'name', 'description'), { entities : COUNT(entities) })
      """
    )
  elif context == 'template':
    cursor = db.aql.execute(
      """
      FOR template IN PrintTemplate
      FILTER template._key == @context_key

      LET entities = (
        FOR edge IN can_use_print_template
          FILTER edge._to == template._id
          return edge
      )

      SORT template.name
      RETURN MERGE(KEEP(template, '_key', 'name', 'description'), { entities : COUNT(entities) })
      """,
      bind_vars=dict(
        context_key=context_key,
      )
    )
  else:
    context_to_collection = dict(
      product='Product',
      phase='Phase',
      step='Step',
      issue_type='IssueType',
      task_type='TaskType',
      position='Position'
    )

    cursor = db.aql.execute(
      """
      FOR edge IN can_use_print_template
        FILTER edge._from == @from_id
        LET template = DOCUMENT(PrintTemplate, edge._to)
        SORT template.name
        RETURN KEEP(template, '_key', 'name', 'description')
      """,
      bind_vars=dict(
        from_id=f'{context_to_collection.get(context)}/{context_key}',
      )
    )

  result = [PrintTemplateRecord(**t) for t in cursor]

  return result


@router.get('/print-template/{template_key}',
    response_model=dict,
    responses={
      404: {"description": "Print template not found"},
      500: {"description": "Template preprocessing error"},
    },
    dependencies=[Depends(auth.verify_token)])
async def get_print_template_details(template_key: str):
  """Retrieve full details for a single print template, including basePdf and schemas.

  Returns the `PrintTemplate` document preprocessed for client use
  (e.g. base64 encoding of embedded PDF data). Use this endpoint when the
  template editor or print renderer needs the complete template definition.

  **Emits:** *(direct query — no event class)*

  **Required scope:** `quality:print-template:read`
  """
  template = db.collection('PrintTemplate').get(template_key)
  return preprocess_template(template)


# Create PrintTemplate
@router.post('/print-template',
    response_model=APIResponse,
    responses={500: {"description": "Database insert error"}},
    dependencies=[Depends(auth.verify_token)])
async def create_print_template(template_data: PrintTemplateRecord):
  """Create a new print template.

  Inserts a `PrintTemplate` document containing the pdfme template definition
  (basePdf, schemas, sampledata). Returns the new template's `_key` in the
  response detail.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:print-template:create`
  """
  try:
    resp = db.collection('PrintTemplate').insert(template_data)
    return APIResponse(
      status_code = 200,
      message = "Print template created successfully",
      detail = dict(template_key=resp['_key'])
    )
  except Exception:
    status_code = 500
    error_str = traceback.format_exc()
    response=dict(
      status=status_code,
      message="There was a problem saving the data into the database. Please contact support if it happens again",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

# Update Print Template
@router.put('/print-template',
    response_model=APIResponse,
    responses={500: {"description": "Database update error"}},
    dependencies=[Depends(auth.verify_token)])
async def update_print_template(template_data: PrintTemplateRecord):
  """Replace a print template's definition.

  Performs a full document update of the `PrintTemplate` identified by
  `template_data._key`. All fields are replaced with the supplied values.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:print-template:create`
  """
  try:
    update = template_data.dict(by_alias=True)
    resp = db.collection('PrintTemplate').update(update)
    return APIResponse(
      status_code = 200,
      message = f"Print template {template_data.key} updated successfully"
    )
  except Exception:
    status_code = 500
    error_str = traceback.format_exc()
    response=dict(
      status=status_code,
      message="There was a problem saving the data into the database. Please contact support if it happens again",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


# Delete Print Template
@router.delete('/print-template/{template_key}',
    response_model=APIResponse,
    responses={500: {"description": "Database delete or edge cleanup error"}},
    dependencies=[Depends(auth.verify_token)])
async def delete_print_template(template_key: str):
  """Delete a print template and all its entity assignment edges.

  Removes the `PrintTemplate` document and all `can_use_print_template` edges
  that reference it, within a single transaction.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:print-template:create`
  """
  try:
    tx = db.begin_transaction(write=['PrintTemplate', 'can_use_print_template'])

    tx.collection('PrintTemplate').delete(template_key)
    tx.collection('can_use_print_template').delete_match(filters=dict(_to=f'PrintTemplate/{template_key}'))

    tx.commit_transaction()

    return APIResponse(message = "Template deleted successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.post('/update-template-assignments',
    response_model=APIResponse,
    responses={500: {"description": "Transaction error updating assignment edges"}},
    dependencies=[Depends(auth.verify_token)])
async def update_template_assignments(updates: list[TemplateAssignmentUpdate]):
  """Batch add or remove print template assignments to/from entities.

  Applies a list of `TemplateAssignmentUpdate` operations atomically:
  - `type='add'`: inserts a `can_use_print_template` edge from the entity to the template.
  - `type='remove'`: deletes the matching edge.

  Used by the template assignment UI to wire templates to products, phases,
  steps, issue types, task types, or positions in a single round-trip.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:print-template:create`
  """

  try:
    tx = db.begin_transaction(write=['can_use_print_template'])

    to_add = [build_template_assignment_record(u) for u in updates if u.type == TemplateAssignmentUpdateType.ADD]
    if to_add:
      tx.collection('can_use_print_template').insert_many(to_add)

    to_remove = [build_template_assignment_record(u) for u in updates if u.type == TemplateAssignmentUpdateType.REMOVE]
    if len(to_remove):
      tx.aql.execute(
        """
        FOR d IN @to_remove
          FOR record IN can_use_print_template
          FILTER
            record._from == d._from
            && record._to == d._to
          REMOVE record IN can_use_print_template
        """,
        bind_vars=dict(to_remove=to_remove)
      )

    tx.commit_transaction()

    return APIResponse(message='Assignments updated correctly')

  finally:
    if tx.transaction_status() != 'committed':
      tx.abort_transaction()


# Print Job Endpoint — NATS Request/Reply

@router.post('/print-job',
    response_model=dict,
    responses={
      200: {"description": "Print job result — check 'ok' field; may be false if the print service is unavailable or timed out"},
    },
    dependencies=[Depends(auth.verify_token)])
async def create_print_job(job: PrintJobRequest):
  """Dispatch a print job to a printer via NATS request/reply.

  Publishes a print job payload to `progress.print.jobs.{printer_key}` and
  waits for a response from the print service worker. The timeout scales with
  `job.copies` to accommodate multi-copy jobs.

  Returns a result dict with `ok: true` on success. On failure, `ok` is false
  and `error` contains one of: `no_service`, `timeout`, or `internal`.

  On successful print, publishes a `PRINT_JOB_COMPLETED` notification on the
  `production` NATS subject.

  **Emits:** *(NATS publish — `progress.print.jobs.{printer_key}`)*

  **Required scope:** `quality:print-template:read`
  """
  subject = f"progress.print.jobs.{job.printer_key}"

  payload = job.model_dump()
  payload["format"] = job.format.value

  base_timeout = job.timeout_seconds or 5
  nats_timeout = (base_timeout * max(job.copies, 1)) + 5

  logger.info(f"NATS request to {subject} (timeout={nats_timeout}s)")
  try:
      response_data = await nats_request(subject, json.dumps(payload), timeout=nats_timeout)
      result = json.loads(response_data)
      logger.info(f"Print job result on {subject}: ok={result.get('ok')}")
  except NoRespondersError:
      logger.warning(f"No print service listening on {subject}")
      result = {"ok": False, "error": "no_service", "detail": "Print service is not running"}
  except TimeoutError:
      result = {"ok": False, "error": "timeout", "detail": "Print service did not respond"}
  except Exception as e:
      logger.error(f"Print job NATS error: {e}")
      result = {"ok": False, "error": "internal", "detail": str(e)}

  if result.get("ok"):
      notification = {
          "subtopic": "production",
          "notification": "PRINT_JOB_COMPLETED",
      }
      subject = subtopic_to_subject("production")
      publish_sync(subject, json.dumps(notification))

  return result
