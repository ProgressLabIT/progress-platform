from events.admin.base_admin import BaseAdmin
from events.wip.wip_unbooked import WIPUnbookedEvent
from events.serial.serial_updated import SerialUpdatedEvent
from models.event import EventInfoModel, EventType
from utils.exceptions import JobIsActiveError, JobHasNoActiveBatchError
from utils.serial import Queries as SerialQueries
from utils.traceability import Queries as TraceabilityQueries


class BatchCanceled(BaseAdmin):

  class InfoModel(EventInfoModel):
    job_key: str

  @classmethod
  def get_tx_collections(self):
    return [
      'Batch',
      'batch_serial',
      'contains',
      'is_in_position',
      'Job',
      'movement',
      'Serial',
      'StepExecutionData',
      'wip',
      'WorkOrder',
      'WorkSession'
    ]

  @classmethod
  def get_event_type(self):
    return EventType.BATCH_CANCELED

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
      canceled = self.event_key
    )
    self.tx.collection('Batch').update(batch_update)

    # Cancel StepExecutionData & WorkSession records
    match = dict(batch_key = batch_key, canceled = None)
    update = dict(canceled = self.event_key)
    self.tx.collection('StepExecutionData').update_match(match, update)
    self.tx.collection('WorkSession').update_match(match, update)

    # Free booked wip
    if not self.job.first_phase:
      WIPUnbookedEvent.create_as_child(self, dict(
        job_key = self.job.key,
        quantity = self.job.active_batch_qt
      ))


    elif self.job.traceability_level:
      # First phase: remove incomplete serials and the relative link.
      # TODO: use a named graph to avoid deleting links explicitly
      self.tx.aql.execute("""
        FOR serial IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
        REMOVE serial IN Serial
      """, bind_vars=dict(batch_key=batch_key))

    if self.job.traceability_level: # both first and following phases
      # Remove obsolete batch_serial records and reset serial data for the phase
      # Remember that serials documents have already been removed
      serials_cursor = self.tx.aql.execute("""
        FOR s, bs IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
        REMOVE bs IN batch_serial
        LET removed = OLD
        RETURN PARSE_IDENTIFIER(OLD._to).key
      """, bind_vars=dict(batch_key=batch_key))

      batch_serial_keys = [serial_key for serial_key in serials_cursor]

      for serial_key in batch_serial_keys:
        SerialUpdatedEvent.create_as_child(self, dict(
          serial_key = serial_key,
          remove_data_from_phases = [self.job.phase_key]
        ))

    # Update Job, removing progress from steps, if any, of former active batch
    # No need to use UPDATE_JOB_PROGRESS query here, as there is no partial batch progress from completed steps
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
