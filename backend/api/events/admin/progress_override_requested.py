from events.admin.base_admin import BaseAdmin, Queries
from events.inventory.movement_reversed import MovementReversedEvent
from events.inventory.movement_completed import MovementCompletedEvent
from utils.dt import timestamp
from utils.inventory import Queries as InventoryQueries
from models.inventory import InventoryMovementType, InventoryMovementReferences
from models.event import EventInfoModel, EventType
from models.production import Job, WorkOrderFull, WorkStatus
from models.traceability import WIP, Batch, WorkSession
from utils.exceptions import (
  JobHasNoAssigneeError,
  JobIsActiveError,
  JobHasActiveBatchError,
  QuantityIncreaseWithTraceabilityNotAllowed,
  WipNotAvailableError,
  MissingSerialKeysError
)
from collections import deque

from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries

class ProgressOverrideRequestedEvent(BaseAdmin):

  class InfoModel(EventInfoModel):
    job_key: str
    new_job_qt_completed: float
    should_adjust_duration: bool | None = True
    quantity_change: int | None = None
    serial_keys_to_remove: list[str] | None = None # only used for traceability


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
      'wip',
      'WorkOrder',
      'WorkSession'
    ]

  @classmethod
  def get_event_type(self):
    return EventType.PROGRESS_OVERRIDE_REQUESTED

  # =================================================================================================
  # MAIN LOGIC
  # =================================================================================================




  # =================================================================================================

  def apply(self):
    """
    Handles progress override requests, including traceability records and WIP management.
    """
    # Validate job state and calculate total duration
    self._init_instance_variables()
    self._validate_job_state()
    self._calculate_and_store_total_duration()

    # Handle either quantity increase or decrease
    if self.info.quantity_change > 0:
        self._handle_quantity_increase()
    else:
        self._handle_quantity_decrease()

    # Update job status and batch available states
    self._handle_job_status()
    self._update_batch_available_states()


  # =================================================================================================
  # LOGIC SECTIONS
  # =================================================================================================

  def _init_instance_variables(self):
    """
    Initializes instance variables for the event
    """
    # Set job, work order and quantity change
    self.job = Job(**self.tx.collection('Job').get(self.info.job_key))
    self.wo = WorkOrderFull(**self.tx.collection('WorkOrder').get(self.job.wo_key))
    self.info.quantity_change = self.info.new_job_qt_completed - self.job.qt_completed

    # Set job bom and traceability components
    self.job_bom = [line for line in self.wo.wo_bom if line.phase_key == self.job.phase_key]
    self.traceability_components = [line for line in self.job_bom if line.traceability_level]

    # Set wip
    self.wip = self.tx.aql.execute(
        TraceabilityQueries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
        bind_vars=dict(job_key=self.info.job_key)
    ).next()

    self.free_wip_qt_upstream = sum(w['quantity'] for w in self.wip['upstream_free_wip'])
    self.free_wip_qt_downstream = sum(w['quantity'] for w in self.wip['downstream_free_wip'])

    ## Global inventory config
    warehouse_enabled = self.tx.collection('Config').get('enable_inventory_management')
    # if config is not set, we assume warehouse is not enabled
    self.handle_inventory = warehouse_enabled is not None and warehouse_enabled.get('value', False)

    ## Product and components inventory config
    product_keys = [self.job.product_key] + [line.component_key for line in self.job_bom]

    self.job_inventory_config = self.tx.aql.execute(
      InventoryQueries.PRODUCTS_INVENTORY_CONFIG,
      bind_vars=dict(product_keys=product_keys)
    ).next()




  def _validate_job_state(self):
    """
    Validates the initial state of the job before allowing progress override.
    Checks:
    1. Job has an assignee
    2. Job is not active
    3. Job has no active batches
    4. Traceability constraints for quantity increases
    """
    # Check job assignment
    if self.job.assigned_to is None:
        raise JobHasNoAssigneeError("You can't declare progress without associating it to a user. Assign the job first.")

    # Check job active status
    if self.job.active:
        raise JobIsActiveError("You can't override progress while the job is active")

    # Check active batch status
    if self.job.active_batch_qt:
        raise JobHasActiveBatchError("You can't override progress if the job has an active batch. Cancel the current batch first.")

    # Check traceability constraints for quantity increases
    if self.job.traceability_level:
      if self.info.new_job_qt_completed > self.job.qt_completed:
        raise QuantityIncreaseWithTraceabilityNotAllowed("You can't increase progress with traceability enabled.")
      if not self.info.serial_keys_to_remove:
        raise MissingSerialKeysError("You must provide the serial keys to remove to override progress with traceability enabled.")
    # Validate quantity change
    if self.info.quantity_change == 0:
        raise ValueError('No quantity change')
    if self.info.new_job_qt_completed > self.job.qt_planned:
        raise ValueError('Quantity is higher than the total planned')


    # Validate wip availability

    if self.info.quantity_change > self.free_wip_qt_upstream and not self.job.first_phase:
        raise WipNotAvailableError("The previous phase has not made enough progress to make this change")

    if self.info.quantity_change < 0 and abs(self.info.quantity_change) > self.free_wip_qt_downstream and not self.job.last_phase:
        raise WipNotAvailableError("You can't reduce the released quantity of this phase below that already completed/started/booked from the following phase")



  # =================================================================================================

  def _calculate_and_store_total_duration(self):
    self.total_duration = self.tx.aql.execute(
        """
        RETURN SUM(
            FOR ws IN WorkSession
            FILTER ws.job_key == @job_key && ws.canceled == null
            RETURN ws.duration
        )
        """,
        bind_vars=dict(job_key=self.job.key)
    ).next()

  # =================================================================================================

  def _handle_quantity_increase(self):
    """Handles creation of new records and WIP management for quantity increases"""
    # Calculate duration if needed
    new_work_session_duration = None
    if not self.info.should_adjust_duration:
        new_work_session_duration = self._handle_time_redistribution()

    # Create forced traceability records
    batch_key, batch_value = self._create_forced_traceability_records(
        quantity=self.info.quantity_change,
        duration=new_work_session_duration
    )

    # Handle upstream WIP
    if not self.job.first_phase:
        self._remove_upstream_wip_for_quantity_increase()

    if self.handle_inventory:
      self._create_inventory_movements_for_forced_batch(batch_key=batch_key)

  # =================================================================================================

  def _handle_quantity_decrease(self):
    """Handles record cancellation and WIP management for quantity decreases"""
    # Cancel batches and get metadata
    canceled_batches, remaining_qt, avg_processing_time = self._cancel_batches_for_quantity_decrease()
    canceled_batches_keys = [b.key for b in canceled_batches]

    # Handle work sessions based on duration adjustment preference
    new_session_duration = self._handle_work_sessions_for_decrease(canceled_batches_keys)

    # Handle downstream WIP
    if not self.job.last_phase:
        self._remove_downstream_wip_for_canceled_batches(canceled_batches_keys)

    # Create compensating batch if needed
    if remaining_qt < 0:
        # Create compensating batch with appropriate duration
        new_batch_key, batch_value = self._create_forced_traceability_records(
            quantity=abs(remaining_qt),
            duration=new_session_duration,
            unit_processing_time=avg_processing_time
        )

        # Update booked WIP references
        self._update_booked_wip_references(canceled_batches_keys, new_batch_key)

    # Handle upstream WIP for quantity decrease
    if not self.job.first_phase:
        self._add_upstream_wip_for_quantity_decrease()

    # TODO: Add serial deletion

    # Revert batch movements
    # revert full movements for all batches except the last one if it's partial
    if self.handle_inventory:
      self._revert_inventory_movements()


  # =================================================================================================

  def _handle_job_status(self):
    """
    Updates job status based on the new quantity completed.
    This method handles both increase and decrease cases:

    For increase:
    - Sets job as STARTED if it was CREATED
    - Sets job as CLOSED if completed equals planned
    - Removes from queue if closed

    For decrease:
    - Sets job as STARTED if it was CLOSED
    - Sets job as CREATED if new quantity is 0
    - Adds back to queue if reopening
    """

    new_job_progress = round(100 * self.info.new_job_qt_completed / self.job.qt_planned)

    self.job_update = dict(
        _key=self.job.key,
        qt_completed=self.info.new_job_qt_completed,
        qt_released=self.info.new_job_qt_completed,
        progress=new_job_progress,
        forced=self.event_key
    )

    if self.info.quantity_change > 0:
        # Set job as started if not already
        if self.job.stage == WorkStatus.CREATED:
            self.job_update['stage'] = WorkStatus.STARTED
            self.job_update['start'] = self.info.timestamp

        # Set job as closed and remove it from queues if necessary
        if self.info.new_job_qt_completed == self.job.qt_planned:
            self.job_update['stage'] = WorkStatus.CLOSED
            self.job_update['end'] = self.info.timestamp
            self.tx.aql.execute(
                ProductionQueries.REMOVE_JOB_FROM_QUEUE,
                bind_vars=dict(
                    target_key=self.job.assigned_to,
                    job_key=self.job.key
                )
            )
    else:  # quantity_change < 0
        # Reopen job if it was closed
        if self.job.stage == WorkStatus.CLOSED:
            self.job_update['stage'] = WorkStatus.STARTED
            self.job_update['end'] = None
            # Readd job to queue and reorder
            self.tx.aql.execute(
                ProductionQueries.ADD_JOB_TO_QUEUE,
                bind_vars=dict(
                    job_key=self.job.key,
                    target_key=self.job.assigned_to
                )
            )
            self.tx.aql.execute(
                ProductionQueries.REORDER_JOB_QUEUES,
                bind_vars=dict(
                    site_key='0',
                    target_key=self.job.assigned_to
                )
            )

        # Reset to created if quantity is 0
        if self.info.new_job_qt_completed == 0:
            self.job_update['stage'] = WorkStatus.CREATED

    # Update job status
    self.tx.collection('Job').update(self.job_update)

  # =================================================================================================

  def _update_batch_available_states(self):
    """Updates batch available states for current and next phases"""
    wip_phases = [self.job.phase_key]

    if not self.job.last_phase:
        wip_phases.append(self.wip['next_phase_key'])

    self.tx.aql.execute(
        TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
        bind_vars=dict(
            wo_key = self.job.wo_key,
            phase_keys = wip_phases
        )
    )


  # =================================================================================================
  # HELPER METHODS
  # =================================================================================================



  def _create_inventory_movements_for_forced_batch(self, batch_key):
    """
    Creates inventory movements for a forced batch
    - Production movement
    - Consumption movements for components

    Method is almost identical to BatchCompletedEvent._process_inventory_changes.
    TODO: refactor to avoid code duplication
    """

    references = InventoryMovementReferences(
      work_order_key = self.job.wo_key,
      job_key = self.info.job_key,
      batch_key = batch_key
    )

    batch_qt = self.info.quantity_change

    # Generate production movement
    if self.job_inventory_config.get(self.job.product_key, False) and self.job.last_phase:
      production_position_key = self._get_output_position_key()

      base_production_data = dict(
        position_to = production_position_key,
        product_key = self.job.product_key,
        movement_type = InventoryMovementType.PRODUCTION,
        references = references
      )

      # Not handling traceability for now
      # if self.info.batch_serial_keys:
      #   for serial_key in self.info.batch_serial_keys:
      #     MovementCompletedEvent.create_as_child(self, dict(
      #       **base_production_data,
      #       qt_confirmed = 1,
      #       qt_planned = 1,
      #       serial_key = serial_key,
      #     ))

      # else:

      MovementCompletedEvent.create_as_child(self, dict(
        **base_production_data,
        qt_confirmed = batch_qt,
        qt_planned = batch_qt,
      ))

    # Generate consumption movements
    component_serials_map = self._get_component_serials(batch_key)

    for line in self.job_bom:
      # Ensure warehouse management is enabled for component
      if self.job_inventory_config.get(line.component_key, False):

        consumption_qt = line.qt * batch_qt

        # If traceability is enabled, generate movements for each serial
        if line.traceability_level is not None:
          line_serials = component_serials_map.get(line.component_key, [])
          if len(line_serials) != consumption_qt:
            raise ValueError("The number of serials provided does not match the batch quantity.")

          for serial_key in line_serials:
            MovementCompletedEvent.create_as_child(self, dict(
              position_from = line.consumption_options.consumption_position_key,
              product_key = line.component_key,
              qt_confirmed = 1,
              qt_planned = 1,
              movement_type = InventoryMovementType.CONSUMPTION,
              references = references,
              serial_key = serial_key,
              reason = f'Progress override requested by user {self.info.user_key},',
            ))

        # If traceability is not enabled, generate movement for the batch
        else:
          MovementCompletedEvent.create_as_child(self, dict(
            position_from = line.consumption_options.consumption_position_key,
            product_key = line.component_key,
            qt_confirmed = line.qt * batch_qt,
            qt_planned = line.qt * batch_qt,
            movement_type = InventoryMovementType.CONSUMPTION,
            references = references,
            reason = f'Progress override requested by user {self.info.user_key},',
          ))


  # =================================================================================================

  def _revert_inventory_movements(self):
    """
    Reverses inventory effects of canceled batches.
    We can't revert specific movements themselves because if overrides have been made, the reference system will not allow us to do so.
    Instead, we revert the effects by creating new movements with the opposite direction.
    """

    if self.job_inventory_config.get(self.job.product_key, False) and self.job.last_phase:
      production_position_key = self._get_output_position_key()
      # revert production movement
      MovementCompletedEvent.create_as_child(self, dict(
        position_from = production_position_key,
        position_to = 'NULL',
        product_key = self.job.product_key,
        movement_type = InventoryMovementType.REVERSAL,
        qt_confirmed = abs(self.info.quantity_change),
        qt_planned = 0,
        reason = f'Progress override requested by user {self.info.user_key},',
        references = InventoryMovementReferences(
          work_order_key = self.job.wo_key,
          job_key = self.info.job_key,
        )
      ))

    # revert consumption movements
    for line in self.job_bom:
      if self.job_inventory_config.get(line.component_key, False):
        MovementCompletedEvent.create_as_child(self, dict(
          position_from = 'NULL',
          position_to = line.consumption_options.consumption_position_key,
          product_key = line.component_key,
          movement_type = InventoryMovementType.REVERSAL,
          qt_confirmed = abs(self.info.quantity_change) * line.qt,
          qt_planned = 0,
          reason = f'Progress override requested by user {self.info.user_key},',
          references = InventoryMovementReferences(
            work_order_key = self.job.wo_key,
            job_key = self.info.job_key,
          )
        ))

  # =================================================================================================


  def _remove_upstream_wip_for_quantity_increase(self):
    """Removes WIP from previous phase for quantity increases"""
    remaining_wip_to_remove = abs(self.info.quantity_change)
    wip_records = deque(self.wip['upstream_free_wip'])
    records_to_delete = deque()

    while remaining_wip_to_remove:
        current_wip = wip_records.popleft()

        if current_wip['quantity'] <= remaining_wip_to_remove:
            records_to_delete.append(current_wip)
            remaining_wip_to_remove -= current_wip['quantity']
        else:
            leftover_wip = current_wip['quantity'] - remaining_wip_to_remove
            wip_update = dict(_key=current_wip['_key'], quantity=leftover_wip)
            self.tx.collection('wip').update(wip_update)
            remaining_wip_to_remove = 0

    self.tx.collection('wip').delete_many(records_to_delete)

  # =================================================================================================

  def _cancel_batches_for_quantity_decrease(self):
    """
    Cancels batches to account for a quantity decrease.

    - Cancels batches from newest to oldest until required quantity is reached
    - Returns data needed for downstream operations

    Returns:
        tuple: (canceled_batch_keys, remaining_quantity, avg_processing_time)
            - canceled_batch_keys: List of keys for canceled batches
            - remaining_quantity: Negative if we canceled more than needed, 0 or positive otherwise
            - avg_processing_time: Average unit processing time (if all batches were canceled)
    """
    # Get non-canceled batches ordered by recency
    job_batches = deque(Batch(**b) for b in self.tx.aql.execute(
        Queries.NON_CANCELED_BATCHES_BY_JOB,
        bind_vars=dict(job_key=self.job.key)
    ))

    remaining_qt_to_remove = abs(self.info.quantity_change)
    batches_to_cancel = deque()

    # Cancel batches until we reach or exceed the target quantity
    while remaining_qt_to_remove > 0:
        current_batch = job_batches.popleft()
        current_batch.canceled = self.event_key
        batches_to_cancel.append(current_batch)
        remaining_qt_to_remove -= current_batch.qt_pass

    # Calculate average processing time if all batches were canceled
    avg_unit_processing_time = None
    if not job_batches:
        avg_unit_processing_time = self._calculate_avg_unit_processing_time()

    # Update batches in database
    batch_updates = [b.model_dump(by_alias=True) for b in batches_to_cancel]
    canceled_batches = [Batch(**b['new']) for b in self.tx.collection('Batch').update_many(batch_updates, return_new=True)]

    return canceled_batches, remaining_qt_to_remove, avg_unit_processing_time

  # =================================================================================================

  def _handle_work_sessions_for_decrease(self, canceled_batches_keys):
    """Handles work session updates for quantity decreases"""
    new_session_duration = None

    if self.info.should_adjust_duration:
        # Flag the work sessions of the canceled batches with `canceled: true`
        self.tx.aql.execute(
            """
            FOR ws IN WorkSession
            FILTER ws.batch_key IN @canceled_batches_keys
            UPDATE ws WITH { canceled: @event_key } in WorkSession
            """,
            bind_vars = dict(
                canceled_batches_keys = canceled_batches_keys,
                event_key = self.event_key
            )
        )
    else:
        # If total duration shouldn't change, redistribute durations
        new_session_duration = self._handle_time_redistribution()

    return new_session_duration

  # =================================================================================================

  def _remove_downstream_wip_for_canceled_batches(self, canceled_batches_keys):
    """Removes downstream WIP for canceled batches"""
    self.tx.aql.execute(
        """
        FOR w IN wip
        FILTER
            w.batch_key IN @canceled_batches_keys
            && PARSE_IDENTIFIER(w._to).collection == 'Phase'
        REMOVE w IN wip
        """,
        bind_vars = dict(canceled_batches_keys=canceled_batches_keys)
    )

  # =================================================================================================

  def _update_booked_wip_references(self, canceled_batches_keys, new_batch_key):
    """Updates WIP records pointing to canceled batches but booked to jobs"""
    self.tx.aql.execute(
        """
        FOR w IN wip
        FILTER
            w.batch_key IN @canceled_batches_keys
            && PARSE_IDENTIFIER(w._to).collection == "Job"
        UPDATE w WITH { batch_key: @new_batch_key } in wip
        """,
        bind_vars = dict(
            canceled_batches_keys = canceled_batches_keys,
            new_batch_key = new_batch_key
        )
    )

  # =================================================================================================

  def _add_upstream_wip_for_quantity_decrease(self):
    """Adds WIP from previous phase for quantity decreases"""
    batches_from_previous_phase = deque(Batch(**b) for b in self.tx.aql.execute(
        """
        FOR b IN Batch
        FILTER
            b.work_order_key == @work_order_key
            && b.phase_key == @phase_key
            && b.canceled == null
        SORT b.end DESC
        RETURN b
        """,
        bind_vars = dict(
            work_order_key = self.job.wo_key,
            phase_key = self.wip['previous_phase_key']
        )
    ))
    wip_to_add = abs(self.info.quantity_change)

    while wip_to_add:
        wip_batch = batches_from_previous_phase.popleft()
        # Wip quantity can be less than batch quantity
        wip_quantity = min([wip_to_add, wip_batch.qt_pass])

        new_wip = WIP(
            _from = f"Phase/{self.wip['previous_phase_key']}",
            _to = f"Phase/{self.job.phase_key}",
            batch_key = wip_batch.key,
            wo_key = self.job.wo_key,
            product_key = self.job.product_key,
            quantity = wip_quantity,
            value = wip_batch.value * wip_quantity / wip_batch.qt_pass,
            active = False,
        )
        self.tx.collection('wip').insert(new_wip)
        wip_to_add -= wip_quantity

  # =================================================================================================

  def _calculate_avg_unit_processing_time(self):
    avg_unit_processing_time = self.tx.aql.execute(
      """
      RETURN AVG(
        FOR b IN Batch
        FILTER b.job_key == @job_key && b.canceled == null
        SORT b.end DESC
        LET total_duration = SUM(
          FOR ws IN WorkSession
          FILTER ws.batch_key == b._key && ws.canceled == null
          RETURN ws.duration
        )
        RETURN total_duration / b.qt_pass
      )
      """,
      bind_vars=dict(job_key=self.job.key)
    ).next()

    return avg_unit_processing_time


  # =================================================================================================

  def _create_forced_traceability_records(self, quantity, duration=None, unit_processing_time=None):
    """
    1. Create new batch with:
    - qt_pass/qt_total: provided quantity
    - start/end: timestamp
    - forced: event id
    - unit_processing_time: average if available or standard time
    - unit_processing_cost: average if available or 0

    2. Create associated work session with:
    - start/end/user_key/user_session_key = None
    - duration: as provided or standard time * quantity_update
    - hourly cost based on user input or weighted average of other sessions
    - forced: event id

    3. Create free wip downstream, if not last phase

    Args:
        quantity: The quantity to use for the new batch and work session
        duration: Optional duration override for the work session
        unit_processing_time: Optional unit processing time override

    ASSUMPTION: Event key, job data etc are already stored in the event class
    """
    if not unit_processing_time:
      unit_processing_time = self._calculate_avg_unit_processing_time() or self.job.parameters.std_processing_time * 1000

    operator_data = self.tx.collection('User').get(self.job.assigned_to)
    hourly_cost = operator_data.get('hourly_cost', 0)

    unit_processing_cost = (0 if hourly_cost is None else hourly_cost) * unit_processing_time
    batch_value = unit_processing_cost * quantity

    new_batch_data = Batch(
      job_key = self.job.key,
      work_order_key = self.job.wo_key,
      phase_key = self.job.phase_key,
      active = False,
      start = self.info.timestamp,
      end = self.info.timestamp,
      qt_pass = quantity,
      qt_total = quantity,
      value = batch_value,
      forced = self.event_key
    )

    new_batch_key = self.tx.collection('Batch').insert(new_batch_data)['_key']

    new_work_sessions_data = WorkSession(
      batch_key = new_batch_key,
      job_key = self.job.key,
      phase_key = self.job.phase_key,
      work_order_key = self.job.wo_key,
      product_key = self.job.product_key,
      hourly_cost = hourly_cost,
      duration = duration or (unit_processing_time * quantity),
      forced = self.event_key
    )

    self.tx.collection('WorkSession').insert(new_work_sessions_data)

    if not self.job.last_phase:
      new_wip = WIP(
        _from = f"Phase/{self.job.phase_key}",
        _to = f"Phase/{self.wip['next_phase_key']}",
        batch_key = new_batch_key,
        wo_key = self.job.wo_key,
        product_key = self.job.product_key,
        quantity = quantity,
        value = batch_value,
        active = False,
      )

      self.tx.collection('wip').insert(new_wip)

    return new_batch_key, batch_value

  # =================================================================================================

  def _handle_time_redistribution(self):
    """
    Handles the creating new work session records with new duration
    for existing batches that are not canceled by the progress override, including:
    1. Canceling existing work sessions
    2. Getting active batches
    3. Creating new work sessions with desired durations

    Returns:
        tuple: (new_batch_key, batch_value) if forced traceability records were created,
              (None, None) otherwise
    """

    # Cancel existing non-canceled work sessions
    ws_cursor = self.tx.aql.execute(
        Queries.CANCEL_JOB_WORK_SESSIONS,
        bind_vars=dict(job_key=self.job.key, event_key=self.event_key)
    )
    canceled_work_sessions = [WorkSession(**ws) for ws in ws_cursor]

    # Get active batches
    active_batches_cursor = self.tx.aql.execute(
        Queries.NON_CANCELED_BATCHES_BY_JOB,
        bind_vars=dict(job_key=self.job.key)
    )
    active_batches = [Batch(**b) for b in active_batches_cursor]

    # If no active batches, create everything through forced traceability records
    if not active_batches:
        # Forced record will be created in the main function
        return
        # unit_processing_time = self._calculate_avg_unit_processing_time() if self.info.quantity_change < 0 else None
        # return self._create_forced_traceability_records(
        #     quantity=self.info.new_job_qt_completed,
        #     duration=self.total_duration if not self.info.should_adjust_duration else None,
        #     unit_processing_time=unit_processing_time
        # )

    # Calculate average hourly cost for the canceled work sessions
    average_hourly_cost = 0 if not canceled_work_sessions else sum(ws.hourly_cost or 0 for ws in canceled_work_sessions) / len(canceled_work_sessions)

    # Create new work sessions with durations and hourly cost based on quantity ratios
    new_work_sessions = []
    total_handled_quantity = 0
    for batch in active_batches:
        quantity_ratio = batch.qt_pass / self.info.new_job_qt_completed
        total_handled_quantity += batch.qt_pass
        work_session = WorkSession(
            batch_key=batch.key,
            job_key=self.job.key,
            phase_key=self.job.phase_key,
            work_order_key=self.job.wo_key,
            product_key=self.job.product_key,
            hourly_cost=average_hourly_cost,
            duration=int(self.total_duration * quantity_ratio),
            forced=self.event_key
        )
        new_work_sessions.append(work_session.model_dump(exclude={'key', 'id', 'rev'}))

    self.tx.collection('WorkSession').insert_many(new_work_sessions)

    outstanding_duration = self.total_duration - sum(ws['duration'] for ws in new_work_sessions)
    return outstanding_duration

  # =================================================================================================

  def _get_component_serials(self, batch_key):
    """
    Gets the component serials for a batch
    Almost identical to BatchCompletedEvent._get_component_serials
    TODO: refactor to avoid code duplication
    """
    query = """
    // if product has no traceability, batch_serials will be empty, so use batch as source
    LET source = LENGTH(@batch_serial_keys)
      ? @batch_serial_keys[* RETURN CONCAT('Serial/', CURRENT)]
      : [CONCAT('Batch/', @batch_key)]
    RETURN MERGE(
      FOR s IN source
        FOR c, e IN 1..1 OUTBOUND s contains
        FILTER !e.replaced
        LET serial_key = c._ke
        COLLECT component_key = c.product_key INTO component_serials
        RETURN { [component_key]: component_serials[*].c._key }
      )
    """
    return self.tx.aql.execute(query, bind_vars=dict(
      batch_serial_keys=self.info.serial_keys_to_remove,
      batch_key=batch_key
    )).next()