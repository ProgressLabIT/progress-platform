from events.admin.base_admin import BaseAdmin, Queries
from utils.dt import timestamp
from utils.exceptions import JobIsActiveError, JobIsNotStartedError
from models.production import Job, WorkStatus
from models.event import EventType, EventInfoModel
from models.traceability import Batch, WorkSession

class TimeOverrideRequested(BaseAdmin):

  class InfoModel(EventInfoModel):
    job_key: str
    new_job_duration: int| None = None # milliseconds

  @classmethod
  def get_tx_collections(cls):
    return ['Batch', 'Job', 'WorkOrder', 'WorkSession']

  @classmethod
  def get_event_type(cls):
    return EventType.TIME_OVERRIDE_REQUESTED

  def apply(self):

    self.job = Job(**self.tx.collection('Job').get(self.info.job_key))

    if self.job.active:
      raise JobIsActiveError("You can't override processing time while the job is still active")

    if self.job.stage == WorkStatus.CREATED:
      raise JobIsNotStartedError("You can't override processing time if the job hasn't started yet")

    # Cancel existing job work sessions, while fetching data
    # for calculation of weighted average hourly cost
    self.tx.aql.execute(
      Queries.CANCEL_JOB_WORK_SESSIONS,
      bind_vars=dict(job_key=self.info.job_key, event_key=self.event_key)
    )

    # Define hourly cost as defined for the operator
    operator_data = self.tx.collection('User').get(self.job.assigned_to)
    hourly_cost = operator_data.get('hourly_cost', 0)

    # Get job batches to update
    match = dict(job_key=self.info.job_key, canceled=None)
    cursor = self.tx.collection('Batch').find(match)
    job_batches = [Batch(**b) for b in cursor]

    # Define new duration, either the one provided or using unit standard time for phase
    if self.info.new_job_duration is not None:
      new_job_duration = self.info.new_job_duration
    else: #
      new_job_duration = self.job.parameters.std_processing_time * self.job.qt_completed

    # Insert forced work session for each batch of the job
    new_work_sessions = []
    batch_updates = []

    for b in job_batches:
      try:
        # Consider also the active batch
        batch_quota = b.qt_total / (self.job.qt_completed + self.job.active_batch_qt)
      # Handle cases where there's active quantity but no completed quantity
      except ZeroDivisionError:
        batch_quota = 1

      batch_duration = int(new_job_duration * batch_quota) # it's milliseconds, no need for decimals here

      batch_update = dict(
        _key = b.key,
        forced = self.event_key
      )

      batch_updates.append(batch_update)

      forced_work_session = WorkSession(
        batch_key = b.key,
        job_key = self.info.job_key,
        work_order_key = self.job.wo_key,
        phase_key = self.job.phase_key,
        product_key = self.job.product_key,
        duration = batch_duration,
        forced = self.event_key,
        hourly_cost = hourly_cost
      )

      new_work_sessions.append(forced_work_session.dict(exclude={'key', 'id', 'rev'}))

    self.tx.collection('WorkSession').insert_many(new_work_sessions)
    self.tx.collection('Batch').update_many(batch_updates)

