from events.admin.base_admin import BaseAdmin
from events.inventory.movement_reversed import MovementReversedEvent
from events.serial.serial_deleted import SerialDeletedEvent
from events.serial.serial_updated import SerialUpdatedEvent
from events.serial.serial_unlinked import SerialUnlinkedEvent
from models.event import EventInfoModel, EventType
from utils.serial import Queries as SerialQueries
from utils.production import update_target_queue
from utils.traceability import Queries as TraceabilityQueries
from utils.exceptions import WipNotAvailableError

class JobResetEvent(BaseAdmin):
  """
  Resets a job to the initial state.
  Checks if there's enough free available downstream wip before next phase, if so:
  - Cancels batches, work sessions and step execution data
  - Unlinks components
  - Cancels serials (if first phase)
  - Removes phase data from serials
  - Adds upstream wip (if not first phase)
  - Deletes downstream wip
  - Reverses movements
  - Updates job as created

  Event key is stored as source for various updates.
  """

  class InfoModel(EventInfoModel):
    job_key: str
    work_order_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_RESET


  def apply(self):
    self._get_job_data()

    # Check there's enough free available downstream wip before next phase
    self.available_wip = self.tx.aql.execute(
      TraceabilityQueries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
      bind_vars = dict(job_key=self.job.key)
    ).next()

    free_wip_qt_downstream = sum(w['quantity'] for w in self.available_wip['downstream_free_wip'])

    # Cancel Batches and store their keys
    self._cancel_batches()

    if not self.job.traceability_level:
      if not self.job.last_phase:
        if free_wip_qt_downstream < self.job.qt_completed:
          raise WipNotAvailableError("You can't reset the job because its output is being worked on in following phases. Reset those jobs first.")
        # Delete downstream wip
        self._reduce_wip(self.available_wip['downstream_free_wip'], self.job.qt_completed)

      if not self.job.first_phase:
        # Add upstream wip
        self._add_upstream_wip()

    else:
      self._handle_serials()

    # Remove serial linkes whether traceability is enabled or not for the output
    self._unlink_components()

    # Cancel StepExecutionData and WorkSession records
    self._cancel_step_execution_data_and_work_sessions()

    # Reverse movements
    self._reverse_movements()

    # Update jobs state
    self._update_jobs_state()



  # =================================================================================================

  def _cancel_batches(self):
    self.job_batch_keys = list(self.tx.aql.execute("""
      FOR b IN Batch
      FILTER b.job_key == @job_key && b.canceled == null
      UPDATE b WITH { canceled: @event_key } IN Batch
      LET updated = NEW
      RETURN updated._key
    """, bind_vars = dict(
      job_key = self.job.key,
      event_key = self.event_key
    )))

  # =================================================================================================

  def _handle_serials(self):
    # Delete batch_serial records returning the serial keys
    self.job_serial_keys = list(self.tx.aql.execute("""
        FOR b IN @batch_keys
        FOR s, e IN 1..1 OUTBOUND CONCAT('Batch/', b) batch_serial
        LET serial_key = s._key
        REMOVE e IN batch_serial
        RETURN serial_key
      """,
      bind_vars=dict(batch_keys=self.job_batch_keys)
    ))

    # Ensure serial wip records are available in the phase buffer downstream and delete them
    if not self.job.last_phase:
      wip_serials_count = self.tx.aql.execute("""
        FOR w IN wip
        FILTER
          w.serial_key IN @job_serial_keys
          AND w._from == CONCAT('Phase/', @phase_key)
          AND PARSE_IDENTIFIER(w._to).collection == 'Phase'
          REMOVE w IN wip
        RETURN 1
        """,
        bind_vars = dict(
          job_serial_keys = self.job_serial_keys,
          phase_key = self.job.phase_key
        ),
        count=True
      ).count()

      if wip_serials_count < len(self.job_serial_keys):
        raise WipNotAvailableError("You can't reset the job because its output is being worked on in following phases. Reset those jobs first.")

    # Cancel Serials (if first phase)
    if self.job.first_phase:
      for serial_key in self.job_serial_keys:
        SerialDeletedEvent.create_as_child(self, dict(serial_key = serial_key))

    else:
      # Delete data from serials
      self._update_serial_data()

      # Make serials available as wip from previous phase
      self._add_upstream_serial_wip()


  # =================================================================================================

  def _update_serial_data(self):
    """Remove phase data from serials and unrelease them if last phase"""
    for s in self.job_serial_keys:
      SerialUpdatedEvent.create_as_child(self, dict(
        serial_key = s,
        remove_data_from_phases = [self.job.phase_key],
        unrelease = self.job.last_phase
      ))

  # =================================================================================================

  def _add_upstream_serial_wip(self):
    # TODO: Use event to add wip
    new_wip_records = [dict(
      _from = f"Phase/{self.available_wip['previous_phase_key']}",
      _to = f"Phase/{self.job.phase_key}",
      wo_key = self.job.wo_key,
      product_key = self.job.product_key,
      quantity = 1,
      serial_key = s,
      active = False
    ) for s in self.job_serial_keys]

    self.tx.collection('wip').insert_many(new_wip_records)

  # =================================================================================================

  def _add_upstream_wip(self):
    # TODO: Use event to add wip
    self.tx.collection('wip').insert(dict(
      _from = f"Phase/{self.available_wip['previous_phase_key']}",
      _to = f"Phase/{self.job.phase_key}",
      wo_key = self.job.wo_key,
      product_key = self.job.product_key,
      quantity = self.job.qt_released,
      active = False
    ))

  # =================================================================================================

  def _unlink_components(self):
    job_component_links = self.tx.aql.execute("""
      FOR link IN contains
      FILTER link.batch_key IN @batch_keys
      RETURN link
    """, bind_vars=dict(batch_keys=self.job_batch_keys))

    temp_links = []

    for link in job_component_links:
      if link['confirmed']:
        parent_type, parent_key = link['_from'].split('/')
        SerialUnlinkedEvent.create_as_child(self, dict(
          child_serial_key = link['_to'].split('/')[-1],
          parent_serial_key = parent_key if parent_type == 'Serial' else None,
          batch_key = parent_key if parent_type == 'Batch' else None,
          reason = f'Job reset by user {self.info.user_key} at {self.info.timestamp}'
        ))
      else:
        temp_links.append(link)

    if len(temp_links) > 0:
      self.tx.collection('contains').delete_many(temp_links)

  # =================================================================================================

  def _cancel_step_execution_data_and_work_sessions(self):
    match = dict(job_key = self.job.key, canceled = None)
    update = dict(canceled = self.event_key)
    self.tx.collection('StepExecutionData').update_match(match, update)
    self.tx.collection('WorkSession').update_match(match, update)

  # =================================================================================================

  def _delete_downstream_wip(self):
    self.tx.aql.execute("""
      FOR w IN wip
      FILTER w.batch_key in @batch_keys
      REMOVE w IN wip
    """, bind_vars=dict(batch_keys=self.job_batch_keys))

  # =================================================================================================

  def _reverse_movements(self):
    movement_to_reverse = self.tx.aql.execute("""
      FOR m IN movement
      FILTER m.references.job_key == @job_key && m.type != 'reversal' && !m.inverse_movement_key
      RETURN m._key
    """, bind_vars=dict(job_key=self.job.key))

    for m in movement_to_reverse:
      MovementReversedEvent.create_as_child(self, dict(original_movement_key = m))

  # =================================================================================================

  def _update_jobs_state(self):

    # Update job as created
    job_update = dict(
      _key = self.job.key,
      qt_completed = 0,
      qt_released = 0,
      stage = 'created',
      start = None,
      end = None,
      progress = 0
    )
    self.tx.collection('Job').update(job_update)

    # If original was closed, put it back into the queue
    if self.job.stage == 'closed':
      update_target_queue(
        job_key=self.job.key,
        target_key=self.job.assigned_to,
        action='add',
        tx=self.tx
      )

    # Update batch available states
    self._update_batch_available_states()
