from events.admin.base_admin import BaseAdmin
from utils.dt import timestamp
from utils.exceptions import JobIsActiveError, JobHasNoActiveBatchError

from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from utils.serial import Queries as SerialQueries


class BatchCanceled(BaseAdmin):

  @classmethod
  def get_write_collections(self):
    return list(set(super().get_write_collections() + ['Batch', 'StepExecutionData', 'WorkSession', 'batch_serial', 'Serial']))

  @classmethod
  def get_read_collections(self):
    return super().get_read_collections()


  def apply(self):
    self._get_job_data()

    if self.job.active:
      raise JobIsActiveError("You can't cancel a batch while it's being worked on")

    if self.job.active_batch_qt == 0:
      raise JobHasNoActiveBatchError("The job has no active batch to cancel")

    # Cancel batch
    batch_key = self.job.active_batch_key
    batch_update = dict(
      _key = batch_key,
      active = False,
      end = self.info.timestamp,
      canceled = self.id
    )
    self.tx.collection('Batch').update(batch_update)

    # Cancel StepExecutionData & WorkSession records
    match = dict(batch_key = batch_key, canceled = None)
    update = dict(canceled = self.id)
    self.tx.collection('StepExecutionData').update_match(match, update)
    self.tx.collection('WorkSession').update_match(match, update)

    # Free booked wip
    if not self.job.first_phase:
      wip_match = dict(_to=f'Job/{self.job.key}', active=True)
      wip_update = dict(_to=f'Phase/{self.job.phase_key}', active=False)
      self.tx.collection('wip').update_match(wip_match, wip_update)
      self.tx.aql.execute(
        TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
        bind_vars=dict(
          wo_key = self.job.wo_key,
          phase_keys = [self.job.phase_key]
        )
      )
    elif self.job.traceability_level:
      # self.job.first_phase = True
      # Remove incomplete serials and the relative link.
      # TODO: use a named graph to avoid deleting links explicitly
      self.tx.aql.execute("""
        FOR serial IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
        REMOVE serial IN Serial
      """, bind_vars=dict(batch_key=batch_key))

    if self.job.traceability_level: # both first and following phases
      # Remove obsolete batch_serial records and reset phase serial data
      # Remember that serials documents have already been removed
      serials_cursor = self.tx.aql.execute("""
        FOR s, bs IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
        REMOVE bs IN batch_serial
        LET removed = OLD
        RETURN PARSE_IDENTIFIER(OLD._to).key
      """, bind_vars=dict(batch_key=batch_key))

      batch_serial_keys = [serial_key for serial_key in serials_cursor]

      self.tx.aql.execute(
        SerialQueries.REMOVE_PHASE_DATA_FROM_SERIALS,
        bind_vars = dict(
          serial_keys = batch_serial_keys,
          phase_keys = [self.job.phase_key]
        )
      )

    # Update Job, removing progress from steps, if any, of former active batch
    job_update = dict(
      _key = self.job.key,
      active_batch_key = None,
      active_batch_qt = 0,
      progress = round(100 * self.job.qt_completed / self.job.qt_planned)
    )

    # Reset as created if batch is first
    if self.job.qt_completed == 0:
      job_update['stage'] = 'created'
      job_update['start'] = None

    self.tx.collection('Job').update(job_update)
