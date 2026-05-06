from events.admin.base_admin import BaseAdmin
from events.wip.wip_unbooked import WIPUnbookedEvent
from events.serial.serial_updated import SerialUpdatedEvent
from events.serial.serial_unlinked import SerialUnlinkedEvent
from events.serial.serial_deleted import SerialDeletedEvent
from models.event import EventInfoModel, EventType
from utils.exceptions import JobIsActiveError, JobHasNoActiveBatchError
from utils.serial import Queries as SerialQueries
from utils.traceability import Queries as TraceabilityQueries


class BatchCanceledEvent(BaseAdmin):

  class InfoModel(EventInfoModel):
    job_key: str
    batch_key: str | None = None
    work_order_key: str | None = None

  @classmethod
  def get_tx_collections(cls):
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
    self.info.batch_key = self.job.active_batch_key
    batch_update = dict(
      _key = self.info.batch_key,
      active = False,
      end = self.info.timestamp,
      canceled = self.event_key
    )
    self.tx.collection('Batch').update(batch_update)

    # Cancel StepExecutionData & WorkSession records
    match = dict(batch_key = self.info.batch_key, canceled = None)
    update = dict(canceled = self.event_key)
    self.tx.collection('StepExecutionData').update_match(match, update)
    self.tx.collection('WorkSession').update_match(match, update)

    # Free booked wip
    if not self.job.first_phase:
      # No need to specify serials as all the serial wip assigned to the job
      # (i.e. belonging to the active batch) will be unbooked
      WIPUnbookedEvent.create_as_child(self, dict(
        job_key = self.job.key,
        quantity = self.job.active_batch_qt
      ))

    if self.job.traceability_level: # both first and following phases
      self._handle_traceability()

    else: # Cancel batch components
      batch_serial_components_keys = self.tx.aql.execute("""
        FOR c IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) contains
        FILTER c.batch_key == @batch_key
        RETURN c._key
      """, bind_vars=dict(batch_key=self.info.batch_key))

      for component_key in batch_serial_components_keys:
        SerialUnlinkedEvent.create_as_child(self, dict(
          serial_key = component_key,
          batch_key = self.info.batch_key,
          reason = 'Batch canceled',
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

    # Recompute NBA for all jobs in this phase now that active_batch_qt is 0
    # and any booked WIP has been freed. WIPUnbookedEvent above also triggers
    # this, but before the job update, so active_batch_qt was still non-zero.
    if not self.job.first_phase:
      self.update_wip_availability_for_phases(phase_keys=[self.job.phase_key])

  # ================================

  def _handle_traceability(self):
    # Remove obsolete batch_serial records and reset serial data for the phase
    # Remember that serials documents have already been removed
    serials_cursor = self.tx.aql.execute("""
      FOR s, bs IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
      REMOVE bs IN batch_serial
      LET removed = OLD
      RETURN PARSE_IDENTIFIER(OLD._to).key
    """, bind_vars=dict(batch_key=self.info.batch_key))

    batch_serial_keys = [serial_key for serial_key in serials_cursor]

    # Remove component links related to the batch
    batch_serial_components_keys = self.tx.aql.execute("""
      FOR s IN @batch_serial_keys
      FOR c, e IN 1..1 OUTBOUND CONCAT('Serial/', s) contains
      FILTER e.batch_key == @batch_key
      REMOVE e IN contains
    """, bind_vars=dict(batch_key=self.info.batch_key, batch_serial_keys=batch_serial_keys))

    if self.job.first_phase:
      # Delete partial serials
      for serial_key in batch_serial_keys:
        SerialDeletedEvent.create_as_child(self, dict(serial_key=serial_key))

    else:
      pass
      # No need to do anything here, as step data gets saved in the serial only when the batch is completed
