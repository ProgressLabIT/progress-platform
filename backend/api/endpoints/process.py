import traceback
from typing import Annotated, List
import os
from uuid import uuid4

from arango import DocumentGetError
from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile, Depends
from utils import auth
from fastapi.encoders import jsonable_encoder

from models.process import *
from models.product import ProductBaseData
from utils import dt
from utils.api import APIResponse
from utils.db import db
from utils.file import FileHandler
from utils.process import *
from utils.exceptions import HTTPError
from utils.media import get_media_path, delete_media


router = APIRouter()


# TODO: optimize queries
@router.get('/operation',
    dependencies=[Depends(auth.verify_token)])
async def get_operation_list():
  def enrich_with_media(op_data):
    operation_media_cursor = db.aql.execute(
      """
      FOR mc IN media_connection
        FILTER mc._from == @operation_id
        RETURN DOCUMENT(mc._to)
      """,
      bind_vars=dict(
        operation_id=op_data['_id']
      )
    )
    operation_media = [media for media in operation_media_cursor]

    for step in op_data.get('default_phase_steps', []):
      if not step.get('media'):
        step['media'] = []
        continue

      step_media = []
      for media in operation_media:
        if media['_key'] in step['media']:
          step_media.append(media)

      step['media'] = step_media

  def enrich_with_templates(op_data):
    for step in op_data.get('default_phase_steps', []):
      if not step.get('print_templates'):
        step['print_templates'] = []
        continue

      step_templates = []
      for template_key in step['print_templates']:
        # account for faulty logic from previous versions
        if not isinstance(template_key, str):
          template_key = template_key['_key']

        template = db.collection('PrintTemplate').get(template_key)
        if template:
          step_templates.append(template)

      step['print_templates'] = step_templates

  def enrich_op_data(op_data):
    op_data['used_for'] = get_products_using_operation(op_data['_key'])
    enrich_with_media(op_data)
    enrich_with_templates(op_data)

    return Operation(**op_data)

  db_list = [enrich_op_data(o) for o in db.collection('Operation').all()]
  # Sort by operation name
  return sorted(db_list, key=lambda o: o.name.lower())


@router.post('/operation',
    dependencies=[Depends(auth.verify_token)])
async def create_operation(new_op_data: Operation):
  try:
    config = db.collection('Config').get('default_operation_parameters')
    if config:
      config = PhaseParameters(**config)
      new_op_data.default_phase_parameters = config

    new_op_record = db.collection('Operation').insert(new_op_data, return_new=True)['new']
    return APIResponse(detail=new_op_record, message="Operation created successfully")

  except:
    status_code = 500
    message = "Could not save new operation, please contact the administrator."
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message=message,
      error=error_str
    )
    raise HTTPException(status_code=status_code, detail=response)


@router.patch('/operation/{operation_key}',
    dependencies=[Depends(auth.verify_token)])
async def update_operation(operation_key: str, operation_update: dict):
  try:
    operation_data = db.collection('Operation').get(operation_key)
  except:
    raise HTTPError(404, "Could not find Operation in the DB")

  try:
    existing_steps = operation_data.get('default_phase_steps', [])
    old_media_keys = {
      media_key
      for step in existing_steps
      for media_key in step.get('media', [])
    }

    new_steps = operation_update.get('default_phase_steps', [])
    new_media_keys = {
      media_key
      for step in new_steps
      for media_key in step.get('media', [])
    }

    media_to_connect = new_media_keys - old_media_keys
    media_to_disconnect = old_media_keys - new_media_keys
  except:
    raise HTTPError(500, "Could not update Operation in the db. Please contact the administrator.")

  if not media_to_connect and not media_to_disconnect:
    try:
      updated_operation = db.collection('Operation').update(
        dict(_key=operation_key, **operation_update),
        return_new=True
      )['new']
      return APIResponse(message="Operation updated successfully", detail=updated_operation)
    except:
      raise HTTPError(500, "Could not update Operation in the db. Please contact the administrator.")

  try:
    tx = db.begin_transaction(write=['Operation', 'Media', 'media_connection'])

    # Handle media connections to the operation so the media is not orphaned due to lack of connections
    # The Media-Operation connection is only used for this purpose, at least for now
    if media_to_connect:
      _from = f'Operation/{operation_key}'
      tx.collection('media_connection').insert_many([
        dict(
          _from=_from,
          _to=f'Media/{media}'
        )
        for media in media_to_connect
      ])

    # Handle media disconnections from the operation
    if media_to_disconnect:
      media_to_disconnect=[f'Media/{media}' for media in media_to_disconnect]

      tx.aql.execute(
        """
        FOR mc IN media_connection
          FILTER mc._from == @operation_id AND mc._to IN @media_to_disconnect
          REMOVE mc IN media_connection
        """,
        bind_vars=dict(
          operation_id=f'Operation/{operation_key}',
          media_to_disconnect=media_to_disconnect
        )
      )

      orphaned_media_ids_cursor = tx.aql.execute(
        """
        FOR disconnected_media_id IN @media_to_disconnect
          FILTER LENGTH(
            FOR mc IN media_connection FILTER mc._to == disconnected_media_id RETURN mc
          ) == 0
          RETURN disconnected_media_id
        """,
        bind_vars=dict(
          media_to_disconnect=media_to_disconnect
        )
      )

      for media_id in orphaned_media_ids_cursor:
        media_key = media_id.split('/')[1]
        try:
          delete_media(media_key)
        except Exception as ex:
          # As delete_media also deletes the file from disk, if we break the flow here by aborting the transaction,
          # the steps will point to Media(db+file) that does not exist anymore. So, we just log a warning and continue.
          print(f'WARNING: Could not delete media {media_key} due to error: {ex}, skipping...')
          continue

    updated_operation = tx.collection('Operation').update(
      dict(_key=operation_key, **operation_update),
      return_new=True
    )['new']

    tx.commit_transaction()

    return APIResponse(message="Operation updated successfully", detail=updated_operation)
  except:
    tx.abort_transaction()
    status_code = 500
    response=dict(
      status_code=status_code,
      message="Could not update Operation in the db. Please contact the administrator.",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)


@router.delete('/operation/{op_key}',
    dependencies=[Depends(auth.verify_token)])
async def delete_operation(op_key: str):

  try:
    is_used_for_products = [p.code for p in get_products_using_operation(op_key)]

  except:
    status_code = 500
    response = dict(
      status_code=status_code,
      message="Couldn't delete Operation from DB due to a server error. Please contact the administrator.",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)

  # Delete operation only if is not used
  if len(is_used_for_products):
    status_code = 403
    response = dict(
      status_code=status_code,
      message=f"Operation cannot be deleted because it is in use in the process of the following products.",
      product_codes=is_used_for_products
    )
    raise HTTPException(status_code=status_code, detail=response)

  else:
    removed_op = db.collection('Operation').delete(dict(_key=op_key), return_old=True)['old']
    return APIResponse(message="Operation successfully deleted", detail=removed_op)


# TODO: Instead of copying it to all phases, selectively copy it to phases using a list of connected products
@router.post('/operation/{operation_key}/copy',
    dependencies=[Depends(auth.verify_token)])
async def copy_operation_to_phases(
  operation_key: str,
  target_product_keys: Annotated[list[str], Body(embed=True)]
):
  operation_data = db.collection('Operation').get(operation_key)
  if not operation_data:
    raise HTTPError(404, "Could not find Operation in the DB")

  try:
    tx = db.begin_transaction(write=['Phase', 'Step', 'can_use_print_template'])

    phases_cursor = tx.aql.execute(
      """
      FOR phase IN Phase
        FILTER phase.operation_key == @operation_key AND phase.product_key IN @target_product_keys
        RETURN phase
      """,
      bind_vars=dict(
        operation_key=operation_key,
        target_product_keys=target_product_keys
      )
    )
    phases = [PhaseRecord(**phase) for phase in phases_cursor]
    phase_updates = []
    for phase in phases:
      new_step_sequence = []
      for step in operation_data['default_phase_steps']:
        step_data = jsonable_encoder(step, exclude={'_key', 'form_fields', 'media', 'print_templates'})

        step_data['form_fields'] = [
          dict(
            field,
            _key=str(uuid4())
          )
          for field in step['form_fields']
        ]

        new_step = tx.collection('Step').insert(step_data, return_new=True)['new']

        step_media = FileHandler.step_media(new_step['_key'])
        media_keys = step.get('media', [])
        media_cursor = tx.aql.execute(
          """
          FOR media IN Media
            FILTER media._key IN @media_keys
            RETURN media
          """,
          bind_vars=dict(
            media_keys=media_keys
          )
        )
        for media in media_cursor:
          try:
            media_path = get_media_path(media['_key'])
            with open(media_path, 'rb') as file:
              await step_media.write_file(file, media['name'])
          except:
            raise HTTPError(500, "Could not copy media to disk")

        print_template_keys = step.get('print_templates', [])
        print_template_updates = []
        for template_key in print_template_keys:
          # account for faulty logic from previous versions
          if not isinstance(template_key, str):
            template_key = template_key['_key']

          print_template_updates.append(dict(
            _from=new_step['_id'],
            _to=f'PrintTemplate/{template_key}'
          ))
        if print_template_updates:
          tx.collection('can_use_print_template').insert_many(print_template_updates)

        new_step_sequence.append(new_step['_key'])

      phase_updates.append(dict(
        _key=phase.key,
        params=operation_data['default_phase_parameters'],
        production_notes=operation_data['default_phase_notes'],
        step_sequence=new_step_sequence
      ))

      # TODO: Copy phase print templates (when implemented)

    updated_phase_results = tx.collection('Phase').update_many(phase_updates, return_new=True)
    updated_phases = [PhaseRecord(**result['new']) for result in updated_phase_results]

    tx.commit_transaction()

    return APIResponse(
      message="Operation successfully copied to all related phases",
      detail=updated_phases
    )
  except Exception as exception:
    tx.abort_transaction()
    if isinstance(exception, HTTPError):
      raise exception
    raise HTTPError(500, "Could not update Operation in the db. Please contact the administrator.")


@router.post('/product/{product_key}/process/copy',
    dependencies=[Depends(auth.verify_token)])
async def copy_process_to_products(
  product_key: str,
  target_product_keys: Annotated[list[str], Body(embed=True)],
):
  try:
    if product_key in target_product_keys:
      raise HTTPError(400, "The source product cannot be in the list of target products")

    tx = db.begin_transaction(write={'Product', *copy_process_to_product_writes})
    current_time = dt.timestamp()

    process_data = tx.aql.execute(
      Queries.GET_PRODUCTION_PROCESS,
      bind_vars=dict(product_key=product_key)
    )
    process = [PhaseData(**phase) for phase in process_data]

    for target_product_key in target_product_keys:
      product_update_result = tx.collection('Product').update(
        dict(
          _key=target_product_key,
          process_phases=copy_process_to_product(tx, process, target_product_key)
        ),
        return_old=True
      )

      # The process has been completely replaced, so all the old phases need to be trashed
      old_phase_sequence = product_update_result['old']['process_phases']
      for phase_to_remove in old_phase_sequence:
        # Flag phase document
        tx.collection('Phase').update(dict(_key=phase_to_remove, trashed=current_time))

        # Flag phase relationships
        tx.aql.execute(
          Queries.TRASH_FLAG_PHASE_RELATIONSHIP,
          bind_vars=dict(phase_key=phase_to_remove, timestamp=current_time)
        )

    tx.commit_transaction()

    return APIResponse(
      message="Process successfully copied to all related products",
    )
  except Exception as exception:
    tx.abort_transaction()
    if isinstance(exception, HTTPError):
      raise exception
    raise HTTPError(500, "Could not copy process to products. Please contact the administrator.")

@router.post('/product/{product_key}/counter/copy',
    dependencies=[Depends(auth.verify_token)])
async def copy_process_to_products(
  product_key: str,
  target_product_keys: Annotated[list[str], Body(embed=True)],
):
  try:
    if product_key in target_product_keys:
      raise HTTPError(400, "The source product cannot be in the list of target products")

    tx = db.begin_transaction(write={'Product', *copy_process_to_product_writes})

    source_product = ProductBaseData( **db.collection('Product').get(product_key))

    products_updates = [dict(_key=p, counter_key=source_product.counter_key) for p in target_product_keys]
    tx.collection('Product').update_many(products_updates)

    tx.commit_transaction()

    return APIResponse(
      message="Counter successfully copied to all related products",
    )
  except Exception as exception:
    tx.abort_transaction()
    if isinstance(exception, HTTPError):
      raise exception
    raise HTTPError(500, "Could not copy counter to products. Please contact the administrator.")


@router.get("/step/{step_key}/media",
    dependencies=[Depends(auth.verify_token)])
async def get_step_media(step_key: str):
  return search_step_media(step_key)



@router.get("/product/{product_key}/process",
    dependencies=[Depends(auth.verify_token)])
async def get_production_process(product_key):

  try:
    process_data = db.aql.execute(
      Queries.GET_PRODUCTION_PROCESS,
      bind_vars=dict(product_key=product_key)
    )

  except Exception as e:
    status_code = 500
    message = "Couldn't fetch data from the db"
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message=message,
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  try:
    results = [PhaseData(**phase) for phase in process_data]

  except Exception as e:
    status_code = 500
    message = "Error validating data from DB"
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message=message,
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  return results



@router.get("/phase",
    dependencies=[Depends(auth.verify_token)])
async def get_phase_data(phase_key: List[str] = Query(...)):
  try:
    phase_db_data = db.collection('Phase').get_many(phase_key)
  except DocumentGetError:
    raise HTTPException(
      status_code=404,
      detail=f"Could not find phase with key {phase_key} in the db"
    )

  return [PhaseRecord(**p) for p in phase_db_data]



@router.put(
  "/product/{product_key}/process",
  response_model = List[PhaseData],
  response_model_exclude = {'step_sequence'},
    dependencies=[Depends(auth.verify_token)]
)
async def update_process(product_key, process: List[PhaseData]):
  tx = db.begin_transaction(write=['Product', 'Phase', 'Step', 'requires'])
  timestamp = dt.timestamp()
  new_phase_sequence = []

  try:
  # LOOP OVER PHASES TO UPDATE DB
    for seq, phase in enumerate(process):

      has_steps = len(phase.steps)

      # Disable step check if no steps are present
      if not has_steps:
        phase.params.step_check = False

      # Insert/replace steps
      for index, s in enumerate(phase.steps):
        # Exclude key field if not present so DB creates new record
        new_step = s.key == None
        exclude_set = { 'key' } if new_step else None
        prepped_step_data = jsonable_encoder(s, by_alias=True, exclude=exclude_set)

        step_update = tx.insert_document('Step',
          prepped_step_data, overwrite=True, return_new=True )

        phase.steps[index] = Step(**step_update['new'])

      phase.step_sequence = [s.key for s in phase.steps]

      # Flag removed steps for deletion by TTL
      old_step_sequence = tx.document(f'Phase/{phase.key}')['step_sequence'] if phase.key else []
      removed_steps = [s for s in old_step_sequence if s not in phase.step_sequence]

      for r in removed_steps:
        tx.collection('Step').update(dict(_key=r, trashed=timestamp))

      # Insert/replace phase
      exclude_set = {'id', 'rev', 'steps'}

      # do not 'export' _id field with value null if none is set, so that the DB
      # will set it automatically
      new_phase = phase.key == None

      if new_phase:
        exclude_set.add('key')

      prepped_phase_data = jsonable_encoder(phase, by_alias=True, exclude=exclude_set)

      db_resp = tx.insert_document('Phase', prepped_phase_data, return_new=True, overwrite=True )['new']

      phase_update = PhaseRecord(**db_resp)

      if new_phase:
        # Insert new ProductPhase relationship
        new_phase_id= phase_update.id
        tx.insert_document('requires', dict(
          _from=f'Product/{product_key}',
          _to=new_phase_id,
          type='ProductPhase'
        ))

        # Insert new PhaseOperation relationship
        tx.insert_document('requires', dict(
          _from=new_phase_id,
          _to=f'Operation/{phase.operation_key}',
          type='PhaseOperation'
        ))

        process[seq].id = phase_update.id
        process[seq].key = phase_update.key

      new_phase_sequence.append(phase_update.key)

    # Update new sequence, returning old one for deletion check
    phase_sequence_update = tx.collection('Product').update(dict(
      _key=product_key,
      process_phases=new_phase_sequence
    ), return_old=True)

    # Flag removed phases (and relationships) for deletion by TTL index
    old_phase_sequence = phase_sequence_update['old']['process_phases']
    removed_phases = [p for p in old_phase_sequence if p not in new_phase_sequence]

    for p in removed_phases:
      # Flag phase document
      tx.collection('Phase').update(dict(_key=p, trashed=timestamp))

      # Flag phase relationships
      tx.aql.execute(
        Queries.TRASH_FLAG_PHASE_RELATIONSHIP,
        bind_vars=dict(phase_key=p, timestamp=timestamp)
      )

    # Commit transaction
    tx.commit_transaction()

    return process

  except Exception as e:
    tx_id = tx.transaction_id
    error_str = traceback.format_exc()
    response = dict(
      exception=e,
      transaction=tx_id,
      error_str=error_str
    )
    tx.abort_transaction()
    raise HTTPException(
      status_code = 500,
      detail = error_str
    )


@router.get('/procedure/{phase_key}',
    dependencies=[Depends(auth.verify_token)])
async def get_phase_procedure(phase_key: str):

  db_steps = db.aql.execute(
    Queries.GET_PHASE_PROCEDURE,
    bind_vars=dict(phase_key=phase_key)
  )

  async def get_full_step_data(step_from_db):
    step_from_db['media'] = search_step_media(step_from_db['_key'])
    return StepWithMediaInfo(**step_from_db)

  return [await get_full_step_data(step) for step in db_steps]


@router.post("/step/{step_key}/media",
    dependencies=[Depends(auth.verify_token)])
async def save_step_media(
  step_key: str,
  media_file: UploadFile = File(...)
):

  new_media = FileHandler.step_media(
    object_key=step_key,
    file=media_file,
    name=media_file.filename
  )

  try:
    await new_media.write_file()
  except:
    error_str = traceback.format_exc()
    status_code = 400
    response = dict(
      status=status_code,
      message='There was an error writing the file to disk',
      error_str=error_str
    )
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  return new_media.name




@router.delete("/step/{step_key}/media/{filename}",
    dependencies=[Depends(auth.verify_token)])
async def delete_step_media(
  step_key: str,
  filename: str
):

  media_to_delete = FileHandler.step_media(
    object_key=step_key,
    name=filename
  )

  try:
    media_to_delete.delete_file()
  except:
    error_str = traceback.format_exc()
    status_code = 400
    response = dict(
      status=status_code,
      message='There was an error deleting the file',
      error_str=error_str
    )
    raise HTTPException(
      status_code = status_code,
      detail = response
    )
