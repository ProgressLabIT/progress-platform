import os
from utils.db import db
from utils.file import FileHandler

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
