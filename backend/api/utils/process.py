import os
from uuid import uuid4

from arango.database import TransactionDatabase
from fastapi.encoders import jsonable_encoder

from utils.db import db
from utils.file import FileHandler
from models.process import PhaseData

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

  phase_sequence = []

  for phase in process:
    step_sequence = []
    for step in phase.steps:
      step_data = step.model_dump(by_alias=True, exclude={'key', 'form_fields', 'media', 'print_templates'})

      step_data['form_fields'] = [
        dict(
          field,
          _key=str(uuid4())
        )
        for field in step.form_fields
      ]

      new_step = tx.collection('Step').insert(step_data, return_new=True)['new']

      step_media = FileHandler.step_media(step.key)
      if os.path.isdir(step_media.folder_path):
        step_media.copy_media(new_step['_key'])

      print_template_keys = tx.aql.execute(
        """
        FOR t IN 1..1 OUTBOUND @step_id can_use_print_template
          RETURN t._key
        """,
        bind_vars=dict(step_id=new_step['_id'])
      )
      print_template_updates = []
      for template_key in print_template_keys:
        print_template_updates.append(dict(
          _from=new_step['_id'],
          _to=f'PrintTemplate/{template_key}'
        ))
      if print_template_updates:
        tx.collection('can_use_print_template').insert_many(print_template_updates)

      step_sequence.append(new_step['_key'])

    new_phase = tx.collection('Phase').insert(
      dict(
        jsonable_encoder(phase, by_alias=True, exclude={'id', 'rev', 'key', 'steps', 'print_templates'}),
        params=phase.params,
        production_notes=phase.production_notes,
        step_sequence=step_sequence
      ),
      return_new=True
    )['new']

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

    phase_bom_cursor = tx.collection('requires').find(
      dict(
        _from=f'Phase/{phase.key}',
        type='BomLine'
      )
    )
    phase_bom = [
      dict(
        jsonable_encoder(line, exclude={'_id', '_key', '_rev'}),
        _from=new_phase['_id']
      )
      for line in phase_bom_cursor
    ]
    if phase_bom:
      tx.collection('requires').insert_many(phase_bom, silent=True)

    # TODO: Copy phase print templates (when implemented)

    phase_sequence.append(new_phase['_key'])

  return phase_sequence


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
    LET phase_id = CONCAT('Phase', @phase_key)
    FILTER r._to == phase_id || r._from == phase_id
    UPDATE r WITH { trashed: @timestamp } IN requires
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
