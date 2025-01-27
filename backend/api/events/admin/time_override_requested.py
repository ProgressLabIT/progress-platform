from events.admin.base_admin import BaseAdmin, Queries
from utils.dt import timestamp
from utils.exceptions import JobIsActiveError, JobIsNotStartedError
from models.production import Job, WorkStatus
from models.traceability import Batch, WorkSession

class TimeOverrideRequested(BaseAdmin):

  @classmethod
  def get_write_collections(self):
    return list(set(super().get_write_collections() + ['Batch', 'WorkSession']))

  @classmethod
  def get_read_collections(self):
    return list(set(super().get_read_collections() + ['User', 'Batch']))


  def apply(self):
    job_key = self.job_key

    self.job = Job(**self.tx.document(f'Job/{job_key}'))

    if self.job.active:
      raise JobIsActiveError("You can't override processing time while the job is still active")

    if self.job.stage == WorkStatus.CREATED:
      raise JobIsNotStartedError("You can't override processing time if the job hasn't started yet")

    # Store work order key for later update
    if not 'work_order_key' in self:
      self.work_order_key = self.job.wo_key

    # Cancel existing job work sessions, while fetching data
    # for calculation of weighted average hourly cost
    self.tx.aql.execute(
      Queries.CANCEL_JOB_WORK_SESSIONS,
      bind_vars=dict(job_key=job_key, event_id=self.id)
    )

    # Define hourly cost as defined for the operator
    operator_data = self.tx.collection('User').get(self.job.assigned_to)
    hourly_cost = operator_data.get('hourly_cost', 0)

    # Get job batches to update
    match = dict(job_key=job_key, canceled=None)
    cursor = self.tx.collection('Batch').find(match)
    job_batches = [Batch(**b) for b in cursor]

    # Define new duration, either the one provided or using unit standard time for phase
    if hasattr(self, 'new_job_duration'):
      new_job_duration = self.new_job_duration
    else: #
      new_job_duration = self.job.parameters.std_processing_time * self.job.qt_completed

    # Insert manual work session for each batch of the job
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
        forced = self.id
      )

      batch_updates.append(batch_update)

      forced_work_session = WorkSession(
        batch_key = b.key,
        job_key = job_key,
        work_order_key = self.work_order_key,
        phase_key = self.job.phase_key,
        product_key = self.job.product_key,
        duration = batch_duration,
        forced = self.id,
        hourly_cost = hourly_cost
      )

      new_work_sessions.append(forced_work_session.dict(exclude={'key', 'id', 'rev'}))

    self.tx.collection('WorkSession').insert_many(new_work_sessions)
    self.tx.collection('Batch').update_many(batch_updates)

