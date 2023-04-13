from collections import deque
from typing import List

from pydantic import BaseModel

from events.shared import EventMeta
from models.production import Job, WorkStatus
from models.traceability import Batch, WIP, WorkSession
from utils.exceptions import JobIsActiveError, JobHasActiveBatchError, JobHasNoAssigneeError, WipNotAvailableError


class Queries:
  CANCEL_JOB_WORK_SESSIONS = """
    FOR ws IN WorkSession
    FILTER ws.job_key == @job_key && !ws.canceled
    UPDATE ws WITH { canceled: @event_id } IN WorkSession
    RETURN NEW
  """

  GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_PHASE = """
    LET current_phase_id = CONCAT('Phase/', @current_phase_key)
    LET process = DOCUMENT(WorkOrder, @work_order_key).phase_sequence
    LET current_phase_index = POSITION(process, @current_phase_key, true)

    LET next_phase_key = @current_phase_key == LAST(process)
      ? null
      : process[current_phase_index + 1]
    LET next_phase_id = CONCAT('Phase/', next_phase_key)

    LET previous_phase_key = @current_phase_key == FIRST(process)
      ? null
      : process[current_phase_index - 1]
    LET previous_phase_id = CONCAT('Phase/', previous_phase_key)

    LET free_up_down_stream_wip_records = (
      for w in wip
      filter
        w.wo_key == @work_order_key
        && w._to in [current_phase_id, next_phase_id]
      return w
    )

    LET upstream_free_wip = (
      FOR w IN free_up_down_stream_wip_records
      FILTER
        w._from == next_phase_id
        && w._to == current_phase_id
      SORT w.batch_key
      RETURN w
    )

    LET downstream_free_wip = (
      FOR w IN free_up_down_stream_wip_records
      FILTER
        w._from == current_phase_id
        && w._to == next_phase_id
      SORT w.batch_key
      RETURN w
    )

    RETURN { upstream_free_wip, downstream_free_wip, next_phase_key, previous_phase_key }
  """



class ProductionAdminEvent:

  # =====================================================================================
  # TIME OVERRIDE
  # =====================================================================================

  TIME_OVERRIDE_REQUESTED = EventMeta(
    collections=['Job', 'Batch', 'WorkSession', 'WorkOrder'],
    action="override_time",
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )

  # -----------------------------------------------------

  def override_time(self):
    job_key = self.info.job_key

    self.job = Job(**self.tx.document(f'Job/{job_key}'))

    # Store work order key for later update
    if not 'work_order_key' in self.info:
      self.info.work_order_key = self.job.wo_key

    # Don't allow updating times on an open job
    job_is_open = self.job.stage != WorkStatus.CLOSED

    if job_is_open:
      raise JobIsActiveError("You are not allowed to override processing time while the job is still open")

    # Cancel existing job work sessions, while fetching data
    # for calculation of weighted average hourly cost
    bind_vars = dict(job_key = job_key, event_id=self.info.id)
    ws_cursor = self.tx.aql.execute(Queries.CANCEL_JOB_WORK_SESSIONS, bind_vars=bind_vars)
    old_work_sessions = [WorkSession(**ws) for ws in ws_cursor]

    # Define hourly cost as provided or as weighted average of the recorded sessions
    if hasattr(self.info, 'hourly_cost'):
      avg_hourly_cost = self.info.hourly_cost
    else:
      # Duration is in milliseconds, cost is based on hours,
      # but conversion is handled going back to hourly cost in the average
      total_recorded_duration = sum(ws.duration for ws in old_work_sessions)
      total_recorded_cost = sum(ws.duration * ws.hourly_cost for ws in old_work_sessions)
      avg_hourly_cost = total_recorded_cost / total_recorded_duration

    # Get job batches to update
    match = dict(job_key=job_key, canceled=None)
    cursor = self.tx.collection('Batch').find(match)
    job_batches = [Batch(**b) for b in cursor]

    # Define new duration, either the one provided or using unit standard time for phase
    # use getattr with default zero to avoid errors in case the value is not provided
    if hasattr(self.info, 'new_job_duration'):
      new_job_duration = self.info.new_job_duration
    else: #
      new_job_duration = self.job.parameters.std_processing_time * self.job.qt_completed

    # Insert manual work session for each batch of the job
    new_work_sessions = []
    batch_updates = []

    for b in job_batches:
      batch_quota = b.qt_total / self.job.qt_completed
      batch_duration = new_job_duration * batch_quota
      new_unit_processing_time = batch_duration / b.qt_total

      batch_update = dict(
        _key = b.key,
        unit_processing_time = new_unit_processing_time,
        unit_processing_cost = new_unit_processing_time * avg_hourly_cost / 3600000, # No. of milliseconds in an hour
        forced = self.info.id
      )

      batch_updates.append(batch_update)

      forced_work_session = WorkSession(
        batch_key = b.key,
        job_key = job_key,
        work_order_key = self.info.work_order_key,
        phase_key = self.job.phase_key,
        product_key = self.job.product_key,
        duration = batch_duration,
        forced = self.info.id,
        hourly_cost = avg_hourly_cost
      )

      new_work_sessions.append(forced_work_session.dict(exclude={'key', 'id', 'rev'}))

    self.tx.collection('WorkSession').insert_many(new_work_sessions)
    self.tx.collection('Batch').update_many(batch_updates)

  # =========================================================================
  # PROGRESS OVERRIDE
  # =========================================================================

  PROGRESS_OVERRIDE_REQUESTED = EventMeta(
    collections=['Job', 'Batch', 'WorkSession', 'WorkOrder', 'wip', 'requires'],
    action='override_progress',
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )

  # -----------------------------------------------------

  def _create_forced_batch_and_work_session(self, quantity):
    """
    Create new batch with:
    - qt_pass/qt_total: provided quantity
    - start/end: timestamp
    - forced: event id
    - unit_processing_time: average if available or standard time
    - unit_processing_cost: average if available or 0

    Then create associated work session with:
    - start/end/user_key/user_session_key = None
    - duration: as provided or standard time * quantity_update
    - hourly cost based on user input or weighted average of other sessions
    - forced: event id

    ASSUMPTION: Event id, job data etc are already stored in the event class
    """
    avg_unit_processing_time = self.tx.aql.execute(
      """
      RETURN AVG(
        FOR b IN Batch
        FILTER b.product_key == @product_key
        SORT b.end DESC
        LIMIT 100
        RETURN b.unit_processing_time
      )
      """,
      bind_vars=dict(product_key=self.job.product_key)
    ).next()

    if avg_unit_processing_time:
      unit_processing_time = avg_unit_processing_time
    else:
      unit_processing_time = self.job.parameters.std_processing_time

    avg_hourly_cost = self.tx.aql.execute(
      """
      LET work_sessions = (
        FOR ws IN WorkSession
        FILTER ws.product_key == @product_key
        SORT ws.end DESC
        LIMIT 100
        RETURN ws
      )

      LET total_time = SUM(work_sessions[*].duration)
      LET total_cost = SUM(work_sessions[* RETURN CURRENT.duration * CURRENT.hourly_cost])

      RETURN total_time ? total_cost / total_time : 0
      """,
      bind_vars = dict(product_key=self.job.product_key)
    ).next()

    unit_processing_cost = avg_hourly_cost * unit_processing_time
    batch_value = unit_processing_cost * quantity_update

    new_batch_data = Batch(
      job_key = self.job.key,
      work_order_key = self.job.wo_key,
      phase_key = self.job.phase_key,
      active = False,
      start = self.info.timestamp,
      end = self.info.timestamp,
      qt_pass = quantity,
      qt_total = quantity,
      unit_processing_time = unit_processing_time,
      unit_processing_cost = unit_processing_cost,
      value = batch_value,
      forced = self.info.id
    )

    new_batch_key = self.tx.collection('Batch').insert(new_batch_data)['_key']

    new_work_sessions_data = WorkSession(
      batch_key = new_batch_key,
      job_key = self.job.key,
      phase_key = self.job.phase_key,
      work_order_key = self.job.wo_key,
      product_key = self.job.product_key,
      hourly_cost = avg_hourly_cost,
      duration = unit_processing_time * quantity_update,
      forced = self.info.id
    )

    self.tx.collection('WorkSession').insert(new_work_sessions_data)

    return new_batch_key, batch_value

  # -----------------------------------------------------

  def override_progress(self):
    bind_vars = dict(
      work_order_key = self.info.work_order_key,
      current_phase_key = self.info.phase_key
    )
    wip = self.tx.aql.execute(
      Queries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_PHASE,
      bind_vars = bind_vars
    ).next()

    self.job = Job(**self.tx.collection('Job').get(self.info.job_key))

    if self.job.assigned_to == None:
      raise JobHasNoAssigneeError("You can't declare progress without associating it to a user. Assign the job first.")

    if self.job.active:
      raise JobIsActiveError("You can't override progress while the job is active")

    if self.job.active_batch_qt:
      raise JobHasActiveBatchError("You can't override progress if the job has an active batch. Cancel the current batch first.")


    # Initialize job update.
    # Will save at the end after enrichment based on override type

    new_job_progress = round(100 * self.info.new_job_qt_completed / self.job.qt_planned)

    job_update = dict(
      _key = self.job.key,
      qt_completed = self.info.new_job_qt_completed,
      qt_released = self.info.new_job_qt_completed,
      progress = new_job_progress,
      forced = self.info.id
    )

    # Check quantity delta
    quantity_update = self.info.new_job_qt_completed - self.job.qt_completed

    # No quantity change
    if not quantity_update:
      raise ValueError('No quantity change')

    # Progress increase
    elif quantity_update > 0:
      if quantity_update > sum(w['quantity'] for w in wip['upstream_free_wip']):
        raise WipNotAvailableError("The previous phase has not made enough progress to make this change")
      else:
        # Set job as started if not already
        if self.job.stage == WorkStatus.CREATED:
          job_update['stage'] = WorkStatus.STARTED

        # Set job as closed if necessary
        if self.info.new_job_qt_completed == self.job.qt_planned:
          job_update['stage'] = WorkStatus.CLOSED
          job_update['end'] = self.info.timestamp

        # 2. Create forced batch and work_session:
        new_batch_key, batch_value = self._create_forced_batch_and_work_session(quantity_update)

        # 3. Delete free wip from previous phase to current (if not first phase)
        if not self.job.first_phase:
          remaining_wip_to_remove = abs(quantity_update)
          wip_records = deque(wip['upstream_free_wip'])
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

        # 4. Create new free wip from current phase to next (if not last phase)
        if not self.job.last_phase:
          new_wip = WIP(
            _from = f"Phase/{self.job.phase_key}",
            _to = f"Phase/{wip['next_phase_key']}",
            batch_key = new_batch_key,
            wo_key = self.job.wo_key,
            product_key = self.job.product_key,
            quantity = quantity_update,
            value = batch_value,
            active = False,
          )
          self.tx.collection('wip').insert(new_wip)

    else: # quantity_update < 0
      if abs(quantity_update) > sum(w['quantity'] for w in wip['downstream_free_wip']):
        raise WipNotAvailableError("You can't reduce the released quantity of this phase below that already completed/started/booked from the following phase")
      else:
        # Reopen job if closed
        if self.job.stage == WorkStatus.CLOSED:
          job_update['stage'] = WorkStatus.STARTED
          job_update['end'] = None

        # Reset job to created status if necessary
        if self.info.new_job_qt_completed == 0:
          job_update['stage'] = WorkStatus.CREATED

        # 2. Flag last N batches with `canceled: true`
        job_batches_cursor = self.tx.aql.execute(
          """
          FOR b IN Batch
          FILTER b.job_key == @job_key
          SORT b.end DESC
          RETURN b
          """,
          bind_vars=dict(job_key=self.job.key)
        )
        job_batches = deque(Batch(**b) for b in job_batches_cursor)
        remaining_qt_to_remove = abs(quantity_update)
        batches_to_cancel = deque()

        # 3. Cancel batches
        # Here we'll cancel only full batches.
        # remaining_qt_to_remove can become negative, will compensate later on
        while remaining_qt_to_remove > 0:
          current_batch = job_batches.popleft()
          current_batch.canceled = self.info.id
          batches_to_cancel.append(current_batch)
          remaining_qt_to_remove -= current_batch.qt_pass

        batch_updates = [b.dict(by_alias=True) for b in batches_to_cancel]
        self.tx.collection('Batch').update_many(batch_updates)
        canceled_batches_keys = [b.key for b in batches_to_cancel]

        # 3. Flag the work sessions of the canceled batches with `canceled: true`
        self.tx.aql.execute(
          """
          FOR ws IN WorkSession
          FILTER ws.batch_key IN @canceled_batches_keys
          UPDATE ws WITH { canceled: @event_id } in WorkSession
          """,
          bind_vars = dict(
            canceled_batches_keys = canceled_batches_keys,
            event_id = self.info.id
          )
        )

        # 4. Delete wip to next phase related to canceled batches (if not last phase)
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

        # 5. If we canceled more than required, create a forced batch/work session to compensate
        if remaining_qt_to_remove < 0:
          new_batch_key, batch_value = self._create_forced_batch_and_work_session(abs(remaining_qt_to_remove))

          # Update potential booked wip from canceled batches
          self.tx.aql.execute(
            """
            FOR w IN wip
            FILTER
              w.batch_key IN @canceled_batches_keys
              && PARSE_IDENTIFIER(w._to).collection == 'Job'
            UPDATE w WITH { batch_key: @new_batch_key }
            """,
            bind_vars = dict(new_batch_key=new_batch_key)
          )

        # 6. Add free wip from previous phase to current (If not first phase)
        # New wip must be associated to batches from the previous phase,
        # starting from the last completed and going backwards
        if not self.job.first_phase:
          cursor = self.tx.aql.execute(
            """
            FOR b IN Batch
            FILTER
              b.work_order_key == @work_order_key
              && b.phase_key == @phase_key
            SORT b.end DESC
            RETURN b
            """,
            bind_vars = dict(
              work_order_key = self.job.wo_key,
              phase_key = wip['previous_phase_key']
            )
          )
          batches_from_previous_phase = deque(Batch(**b) for b in cursor)
          wip_to_add = quantity_update
          new_wip_records = deque()

          while wip_to_add:
            wip_batch = batches_from_previous_phase.popleft()
            # Wip quantity can be less than batch quantity
            wip_quantity = min([wip_to_add, wip_batch.qt_pass])
            new_wip = WIP(
              _from = f"Phase/{wip['previous_phase_key']}",
              _to = f"Phase/{self.job.phase_key}",
              batch_key = wip_batch.key,
              wo_key = self.job.wo_key,
              product_key = self.job.product_key,
              quantity = wip_quantity,
              value = wip_batch.value * wip_quantity / wip_batch.qt_pass,
              active = False,
            )
            new_wip_records.append(new_wip)
            wip_to_add -= wip_quantity

          self.tx.collection('wip').insert_many(new_wip_records)

    self.tx.collection('Job').update(job_update)




  # ========================================================================

  def flag_job_as_forced(self):
    job_update = dict(_key=self.info.job_key, forced=True)
    self.tx.collection('Job').update(job_update)

  # REMEMBER TO WIRE IN WORK ORDER UPDATE!!!


