from events.admin.base_admin import BaseAdmin, Queries
from utils.dt import timestamp
from models.event import EventInfoModel, EventType
from models.production import Job, WorkStatus
from models.traceability import WIP, Batch, WorkSession
from utils.exceptions import JobHasNoAssigneeError, JobIsActiveError, JobHasActiveBatchError, QuantityOverrideForSerialsNotAllowed, WipNotAvailableError
from collections import deque

from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries

class ProgressOverrideRequested(BaseAdmin):

  class InfoModel(EventInfoModel):
    job_key: str
    new_job_qt_completed: int
    should_adjust_duration: bool | None = True
    quantity_change: int | None = None


  @classmethod
  def get_tx_collections(self):
    return ['Batch', 'WorkOrder','WorkSession', 'wip', 'Job']

  @classmethod
  def get_event_type(self):
    return EventType.PROGRESS_OVERRIDE_REQUESTED

  # =================================================================================================
  # MAIN APPLY LOGIC
  # =================================================================================================

  def apply(self):
    """
    Handles:
    - the cancelling of obsolete batches and worksessions
    - the creation of forced batches and work sessions
    - the redistribution of work sessions with new durations
    - the handling (adding/removing) of wip from previous phase and to next phase
    """

    # ------------------------------------------------------------------------------------------------
    # Set self.job, self.wip, self.quantity_change and raise errors if needed
    # ------------------------------------------------------------------------------------------------
    self._validate_job_state()

    # ------------------------------------------------------------------------------------------------
    # Calculate and store total duration for later use
    # ------------------------------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------------------------------
    # Quantity increase
    # ------------------------------------------------------------------------------------------------

    if self.info.quantity_change > 0:
        """
        If total duration should change, then we simply create a new batch with the new quantity and duration

        If total duration shouldn't change, then we need to cancel all work sessions and recreate them with the new durations
        1. Cancel all work sessions
        2. Distribute total processing time evenly in each batch
        3. Create a new work session for each existing batch with the split duration
        """

        new_work_session_duration = None # Will be calculated in _create_forced_traceability_records if not set
        if not self.info.should_adjust_duration:
            new_work_session_duration = self._handle_time_redistribution()

        # Create forced batch, work session and wip
        self._create_forced_traceability_records(quantity=self.info.quantity_change, duration=new_work_session_duration)

        # Delete free wip from previous phase to current (if not first phase)
        if not self.job.first_phase:
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


    # ------------------------------------------------------------------------------------------------
    # Quantity decrease
    # ------------------------------------------------------------------------------------------------

    else:
        """
        1. Cancel full batches until reaching the required quantity or more
        2. Cancel the relative work sessions
        4. If we canceled more than required, create a forced batch/work session/wip to compensate
        3. Delete wip to next phase related to canceled batches (if not last phase)
        5. Add free wip from previous phase to current (If not first phase)
        """
        # ------------------------------------------------------------------------------------------------
        # 1. Cancel full batches until reaching the required quantity or more
        # ------------------------------------------------------------------------------------------------
        job_batches = deque(Batch(**b) for b in self.tx.aql.execute(
            Queries.NON_CANCELED_BATCHES_BY_JOB,
            bind_vars=dict(job_key=self.job.key)
        ))
        remaining_qt_to_remove = abs(self.info.quantity_change)
        batches_to_cancel = deque()

        # Here we cancel only full batches, one at a time, picking from the latest completed batches.
        # Remaining_qt_to_remove can become negative, will compensate later on
        while remaining_qt_to_remove > 0:
            current_batch = job_batches.popleft()
            current_batch.canceled = self.event_key
            batches_to_cancel.append(current_batch)
            remaining_qt_to_remove -= current_batch.qt_pass

        avg_unit_processing_time = None

        # If we end up canceling all batches, calculate the average unit processing time before executing the canceling query
        if not job_batches:
            avg_unit_processing_time = self._calculate_avg_unit_processing_time()

        batch_updates = [b.model_dump(by_alias=True) for b in batches_to_cancel]
        self.tx.collection('Batch').update_many(batch_updates)
        canceled_batches_keys = [b.key for b in batches_to_cancel]

        # If more quantity is canceled than desired, we'll create a forced batch/work session/wip to compensate later on,
        # after the work sessions and wip for next phase have been canceled


        # ------------------------------------------------------------------------------------------------
        # 2. Cancel the work sessions
        # ------------------------------------------------------------------------------------------------
        # If total duration should change, then we need to cancel only the work sessions of the canceled batches

        new_session_duration = None # Will be calculated in _create_forced_traceability_records if not set

        if self.info.should_adjust_duration:
            # 3. Flag the work sessions of the canceled batches with `canceled: true`
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
            # If total duration shouldn't change, then we need to cancel all work sessions and recreate them with the new durations
            # new_session_duration will be zero if no excess quantity was canceled
            new_session_duration = self._handle_time_redistribution()

        # ------------------------------------------------------------------------------------------------
        # 4. Delete wip to next phase related to canceled batches (if not last phase)
        # ------------------------------------------------------------------------------------------------
        if not self.job.last_phase:
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

        # ------------------------------------------------------------------------------------------------
        # 5. If we canceled more than required, create a forced batch/work session/wip to compensate
        # ------------------------------------------------------------------------------------------------
        if remaining_qt_to_remove < 0:
            new_batch_key, batch_value = self._create_forced_traceability_records(
                quantity=abs(remaining_qt_to_remove),
                duration=new_session_duration,
                unit_processing_time=avg_unit_processing_time
            )

            # Update potential booked wip from canceled batches
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

        # ------------------------------------------------------------------------------------------------
        # 6. Add free wip from previous phase to current (If not first phase)
        # ------------------------------------------------------------------------------------------------
        # New wip must be associated to batches from the previous phase,
        # starting from the last completed and going backwards
        if not self.job.first_phase:
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

    # ------------------------------------------------------------------------------------------------
    # Update job status
    # ------------------------------------------------------------------------------------------------
    self._handle_job_status()


    # ------------------------------------------------------------------------------------------------
    # Update batch available state for current and next phase (if present)
    # ------------------------------------------------------------------------------------------------
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


    # ------------------------------------------------------------------------------------------------
    # END OF APPLY LOGIC
    # ------------------------------------------------------------------------------------------------





  # =================================================================================================
  # HELPER METHODS
  # =================================================================================================

  def _validate_job_state(self):
    """
    Validates the initial state of the job before allowing progress override.
    Checks:
    1. Job has an assignee
    2. Job is not active
    3. Job has no active batches
    4. Traceability constraints for quantity increases

    Raises:
        JobHasNoAssigneeError: If job has no assigned user
        JobIsActiveError: If job is currently active
        JobHasActiveBatchError: If job has an active batch
        QuantityOverrideForSerialsNotAllowed: If trying to increase progress with traceability enabled
    """
    # Get and store job data
    self.job = Job(**self.tx.collection('Job').get(self.info.job_key))

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
    if self.job.traceability_level and self.info.new_job_qt_completed > self.job.qt_completed:
        raise QuantityOverrideForSerialsNotAllowed("You can't increase progress with traceability enabled.")

    # Validate quantity changes
    self.info.quantity_change = self.info.new_job_qt_completed - self.job.qt_completed
    if not self.info.quantity_change:
        raise ValueError('No quantity change')
    elif self.info.new_job_qt_completed > self.job.qt_planned:
        raise ValueError('Quantity is higher than the total planned')

    # Validate wip availability
    self.wip = self.tx.aql.execute(
        TraceabilityQueries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
        bind_vars=dict(job_key=self.info.job_key)
    ).next()

    self.free_wip_qt_upstream = sum(w['quantity'] for w in self.wip['upstream_free_wip'])
    self.free_wip_qt_downstream = sum(w['quantity'] for w in self.wip['downstream_free_wip'])

    if self.info.quantity_change > self.free_wip_qt_upstream and not self.job.first_phase:
        raise WipNotAvailableError("The previous phase has not made enough progress to make this change")

    if self.info.quantity_change < 0 and abs(self.info.quantity_change) > self.free_wip_qt_downstream and not self.job.last_phase:
        raise WipNotAvailableError("You can't reduce the released quantity of this phase below that already completed/started/booked from the following phase")

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