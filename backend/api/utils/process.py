import os
from uuid import uuid4

from arango.database import TransactionDatabase
from fastapi.encoders import jsonable_encoder

from utils.db import db
from utils.file import FileHandler
from utils.dt import timestamp
from models.bom import BomLineWriteOut
from models.process import PhaseData
from models.form import FormFieldDefinition



class Queries:
  GET_PRODUCTION_PROCESS = """
    LET phases = DOCUMENT(Product, @product_key).process_phases

    FOR phase_key in phases
      LET phase = DOCUMENT(Phase, phase_key)

      LET steps = (
        FOR step_key IN phase.step_sequence
        RETURN UNSET(DOCUMENT(Step, step_key), '_id', '_rev')
      )

      LET print_templates = (
        FOR t IN 1..1 OUTBOUND CONCAT('Phase/', phase_key) can_use_print_template
        RETURN KEEP(t, '_key', 'name', 'description')
      )

      LET phase_data = MERGE(
        phase,
        {
          steps,
          print_templates
        }
      )
      RETURN phase_data
  """

  TRASH_FLAG_PHASE_RELATIONSHIP = """
    FOR r IN requires
    LET phase_id = CONCAT('Phase/', @phase_key)
    FILTER r._to == phase_id || r._from == phase_id
    UPDATE r WITH { trashed: @timestamp } IN requires
    RETURN OLD
  """

  GET_PHASE_PROCEDURE = """
    LET step_sequence = FIRST(
      FOR p IN Phase
      FILTER p._key == @phase_key
      RETURN p.step_sequence
    )

    FOR s in step_sequence
    RETURN s
  """


  GET_PROCESS_TASKS = """
    FOR p IN Product
    FILTER p._key == @product_key
    FOR t IN NOT_NULL(p.process_tasks, [])
    LET task_type = FIRST(
      FOR tt IN TaskType
      FILTER tt._key == t.task_type_key
      RETURN tt
    )
    RETURN MERGE(t, {
      task_type_name: task_type.name,
      task_type_icon: task_type.icon
    })
  """



def delete_phase(tx: TransactionDatabase, phase_key: str):
  current_time = timestamp()

  # Flag phase document
  tx.collection('Phase').update(dict(_key=phase_key, trashed=current_time))

  # Flag phase relationships
  trashed = list(tx.aql.execute(
    Queries.TRASH_FLAG_PHASE_RELATIONSHIP,
    bind_vars=dict(phase_key=phase_key, timestamp=current_time)
  ))

  return trashed



def search_step_media(step_key: str):

  step_media = FileHandler.step_media(step_key)
  media_folder_exists = os.path.isdir(step_media.folder_path)

  if (media_folder_exists):
    return step_media.get_folder_contents()

  else:
    return []



def get_products_using_operation(op_key):
  cursor = db.aql.execute("""
      FOR v IN 2..2 INBOUND CONCAT('Operation/', @op_key) requires
      FILTER PARSE_IDENTIFIER(v._id).collection == 'Product'
      RETURN KEEP(v, 'code', '_key')
    """, bind_vars=dict(op_key=op_key))

  return [product for product in cursor]

# to be used in db.begin_transaction(write=...)
copy_process_to_product_writes = {
  'Phase',
  'Step',
  'can_use_print_template',
  'requires'
}
def copy_process_to_product(
  tx: TransactionDatabase,
  process: list[PhaseData],
  product_key: str
) -> list[str]:
  """
  Use with copy_process_to_product_writes in db.begin_transaction(write=...) and feed the transaction object as the first argument

  Creates a new process for the product_key based on the given process and returns the phase sequence of the new process
  Use the returned phase sequence to update the Product.process_phases field
  """

  # Delete phases in the old process
  try:
    old_phases = tx.collection('Product').get(product_key)['process_phases']
  except StopIteration:
    raise HTTPException(status_code=404, detail=f"Product {product_key} not found")

  for phase_key in old_phases:
    delete_phase(tx, phase_key)

  phase_sequence = []
  last_phase_key = process[-1].key

  for phase in process:
    is_last_phase = phase.key == last_phase_key
    step_sequence = []
    for step in phase.steps:
      step_data = step.model_dump(by_alias=True, exclude={'key', 'form_fields', 'media', 'print_templates'})

      # Recreate the form fields with new keys
      step_data['form_fields'] = [
        FormFieldDefinition(
          # Overwrite the key with a new uuid (exclude used with attribute name, add it using the alias)
          **field.model_dump(by_alias=True, exclude={'key'}),
          _key=str(uuid4())
        ).model_dump(by_alias=True)
        for field in step.form_fields
      ]

      new_step = tx.collection('Step').insert(step_data, return_new=True)['new']

      step_media = FileHandler.step_media(step.key)
      if os.path.isdir(step_media.folder_path):
        step_media.copy_media(new_step['_key'])

      print_template_ids = tx.aql.execute(
        """
        FOR t IN 1..1 OUTBOUND @step_id can_use_print_template
        RETURN t._id
        """,
        bind_vars=dict(step_id=f'Step/{step.key}')
      )
      print_template_updates = []
      for template_id in print_template_ids:
        print_template_updates.append(dict(
          _from=new_step['_id'],
          _to=template_id
        ))
      if print_template_updates:
        tx.collection('can_use_print_template').insert_many(print_template_updates)

      step_sequence.append(new_step['_key'])

    # Create the new phase by overriding the original phase with the new step sequence and product key
    new_phase = tx.collection('Phase').insert(
      dict(
        jsonable_encoder(phase, by_alias=True, exclude={'id', 'rev', 'key', 'steps', 'print_templates'}),
        step_sequence=step_sequence,
        product_key=product_key
      ),
      return_new=True
    )['new']


    # Create the new phase relationships
    tx.collection('requires').insert(dict(
      _from=f'Product/{product_key}',
      _to=new_phase['_id'],
      type='ProductPhase'
    ))

    tx.collection('requires').insert(dict(
      _from=new_phase['_id'],
      _to=f'Operation/{phase.operation_key}',
      type='PhaseOperation'
    ))


    # HANDLE BOM LINES
    # Existing bom lines are linked to the old product phases and must be updated
    # It's not sensible to require explicit association to new phases, so we'll link to the last phase by default
    if is_last_phase:

      # Fetch existing bom lines
      bom_lines = list(tx.aql.execute(
        """
        FOR bom_line IN requires
        FILTER bom_line._from IN @phase_ids AND bom_line.type == 'BomLine'
        RETURN bom_line
        """,
        bind_vars=dict(phase_ids=[f'Phase/{phase_key}' for phase_key in old_phases])
      ))

      # Create new bom lines with the new phase id
      new_bom_lines = [BomLineWriteOut(
        component_id=line['_to'],
        phase_id=new_phase['_id'],
        type='BomLine',
        qt=line['qt'],
        traceability_level=line.get('traceability_level'),
        consumption_options=line.get('consumption_options'),
        extra=line.get('extra')
      ).model_dump(by_alias=True) for line in bom_lines]

      tx.collection('requires').insert_many(new_bom_lines, silent=True)

    # TODO: Copy phase print templates (when implemented)

    phase_sequence.append(new_phase['_key'])

  return phase_sequence
