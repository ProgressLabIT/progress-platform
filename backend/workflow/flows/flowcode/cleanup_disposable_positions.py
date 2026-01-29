
from prefect import flow
from prefect.schedules import Cron

from common.utils import connect_to_progress_db




flag_positions_as_deleted = """
  FOR p IN Position
  FILTER p.disposable == true
    && p.deleted != true
    && p._key NOT IN ['IN', 'OUT', 'NULL'] // Should never be disposable, but for safety

  // Ensure there are no contents (inventory or non-deleted child positions)
  LET is_empty = LENGTH(
    FOR v IN 1..1 INBOUND p is_in_position
      FILTER
        IS_SAME_COLLECTION(Product, v)  // inventory
        || (IS_SAME_COLLECTION(Position, v) && v.deleted != true) // non-deleted child positions
      RETURN 1
  ) == 0

  FILTER is_empty == true

  UPDATE p WITH { deleted: true } IN Position
  LET old = OLD
  RETURN old.code
"""



@flow(name="Cleanup disposable positions", log_prints=True)
def main():
  """
  Delete positions that are marked as disposable and have no contents.
  The behaviour mirrors the API: positions are soft-deleted (deleted=true)
  and their hierarchy link in is_in_position is removed, but the Position
  document itself is not hard-deleted.
  """
  try:
    print("Connecting to Progress DB...")
    db = connect_to_progress_db()
  except Exception as e:
    print(f"Error connecting to Progress DB: {e}")
    return False

  print("Searching for disposable, empty positions to delete...")
  deleted_position_codes = list(db.aql.execute(flag_positions_as_deleted))
  if len(deleted_position_codes) > 0:
    print(f"Found {len(deleted_position_codes)} disposable positions to delete")
    print(f"Position codes: {', '.join(deleted_position_codes)}")
  else:
    print("No disposable positions to delete")

  return True


# Run every 2 hours on weekdays
schedule = Cron("0 */2 * * mon-fri")


