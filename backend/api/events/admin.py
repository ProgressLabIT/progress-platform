from pydantic import BaseModel

from events.shared import EventMeta
from models.production import Job, WorkStatus
from models.traceability import Batch, WIP, WorkSession
from utils.exceptions import JobIsActiveError
from utils.traceability import Queries



class Queries:
  CANCEL_JOB_WORK_SESSIONS = """
    FOR ws IN WorkSession
    FILTER ws.job_key == @job_key && !ws.canceled
    UPDATE ws WITH { canceled: @event_id } IN WorkSession
    RETURN NEW
  """



class ProductionAdminEvent:

  TIME_OVERRIDE_REQUESTED = EventMeta(
    collections=['Job', 'Batch', 'WorkSession', 'WorkOrder'],
    action="override_time",
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )

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

  # =====================================================================================

  PROGRESS_OVERRIDE_REQUESTED = EventMeta(
    collections=['Job', 'Batch', 'WorkSession', 'WorkOrder', 'wip', 'requires'],
    action='override_progress',
    post_processing=['update_work_order', 'flag_job_as_forced'],
    event_first = True
  )

  def override_progress(self):
    bind_vars = dict(
      work_order_key = self.info.work_order_key,
      current_phase_key = self.info.phase_key
    )
    wip = self.tx.aql.execute(
      Queries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_PHASE,
      bind_vars = bind_vars
    ).next()

    self.job = self.tx.collection('Job').get(self.info.job_key)
    quantity_update = self.info.new_qt_completed - self.job.qt_completed

    # Completed quantity increase
    if quantity_update > 0:
      if quantity_update <= wip['upstream_free_wip']:
        pass

        # 1. Store new data in job:
        # - new quantity completed/released
        # - status (if closed)
        # - end: as provided or event timestamp (if closed)
        # - note: updated by ...

        # 2. Create new batch with:
        # - qt_total: quantity_update
        # - duration: as provided or standard time * quantity_update
        # - forced: event id

        # 3. Create a new WorkSession with:
        # - start/end/user_key/user_session_key = None
        # - duration: as provided or standard time * quantity_update
        # - hourly cost based on user input or weighted average of other sessions
        # - forced: event id

        # 4. Delete free wip from previous phase to current (if not first phase)

        # 5. Create new free wip from current phase to next (if not last phase)



      else:
        raise WipNotAvailableError("The previous phase has not made enough progress to make this change")

    elif quantity_update < 0:
      if quantity_update <= wip['downstream_free_wip']:
        pass

        # 1. Store new data in job:
        # - new quantity completed/released
        # - status (if reopened or fully restarted)
        # - start: null (if fully restarted)
        # - note: updated by...

        # 2. Flag last N batches with `canceled: true`

        # 3. Flag the work sessions of the canceled batches with `canceled: true`

        # 4. Delete free wip from current phase to next (if not last phase)

        # 5. Add free wip from previous phase to current (If not first phase)

      else:
        raise WipNotAvailableError("You can't reduce the released quantity of this phase below that already completed/started/booked from the following phase")



  # =====================================================================================

  def flag_job_as_forced(self):
    job_update = dict(_key=self.info.job_key, forced=True)
    self.tx.collection('Job').update(job_update)

  # REMEMBER TO WIRE IN WORK ORDER UPDATE!!!


