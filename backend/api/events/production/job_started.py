from events.production.base_production import BaseProductionEvent
from events.production.batch_created import BatchCreatedEvent
from events.work_session.work_session_created import WorkSessionCreatedEvent
from models.event import EventInfoModel, EventType
from models.production import Job, WorkStatus
from models.traceability import *
from utils.exceptions import JobHasNoAssigneeError, JobIsStartedError
from utils.production import Queries as ProductionQueries
from utils.production import update_target_queue


class JobStartedEvent(BaseProductionEvent):

  class InfoModel(EventInfoModel):
    job_key: str

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.JOB_STARTED

  def apply(self):
    self._get_job_data()

    # Check job hasn't been started already
    if self.job.stage != WorkStatus.CREATED:
      raise JobIsStartedError('Job has already been started')

    # Check config for unassigned jobs
    show_unassigned_jobs_to_operators = self.tx.collection('Config').get('show_unassigned_jobs_to_operators')
    can_self_assign = show_unassigned_jobs_to_operators.get('value', True) if show_unassigned_jobs_to_operators is not None else True
    add_to_queue = False

    if self.job.assigned_to is None:
      if not can_self_assign:
        raise JobHasNoAssigneeError('Unassigned jobs cannot be worked on as config "show_unassigned_jobs_to_operators" is false')
      else:
        add_to_queue = True

    # Create new batch and store _key in Event.info
    self.batch = BatchCreatedEvent.create_as_child(context=self, new_event_data=dict(
      job_key = self.info.job_key,
      phase_key = self.info.phase_key,
      work_order_key = self.info.work_order_key,
      product_key = self.info.product_key
    ))

    self.info.batch_key = self.batch.key

    # Create new WorkSession and store _key in Event.info
    self.work_session = WorkSessionCreatedEvent.create_as_child(self, dict(
      job_key = self.info.job_key,
      batch_key = self.info.batch_key,
      work_order_key = self.info.work_order_key,
      phase_key = self.info.phase_key,
      product_key = self.info.product_key,
      user_key = self.info.user_key,
      user_session_key = self.info.user_session_key
    ))

    self.info.work_session_key = self.work_session.key

    # Update job
    job_update=dict(
      _key = self.info.job_key,
      start = self.info.timestamp,
      stage = WorkStatus.STARTED,
      last_work_session_started = self.info.work_session_key,
      active_batch_key = self.batch.key,
      active_batch_qt = self.batch.qt_total,
      active = True,
      assigned_to = self.info.user_key,
      last_online = self.info.timestamp
    )
    self.job = Job(**self.tx.collection('Job').update(job_update, return_new=True)['new'])

    if add_to_queue:
      update_target_queue(
        job_key = self.info.job_key,
        target_key = self.info.user_key,
        action = 'add',
        tx = self.tx
      )

    self.response = dict(
      message = f"Job {self.info.job_key} started",
      batch_data = self.get_batch_execution_data(),
      job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.job.key)).next()
    )


