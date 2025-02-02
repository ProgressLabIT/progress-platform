from events.production.base_production import BaseProduction, BaseProductionModel
from models.traceability import *
from models.production import Job, WorkStatus
from utils.exceptions import JobIsStartedError, JobHasNoAssigneeError
from utils.production import update_target_queue
from utils.db import model_to_db_dict
from utils.traceability import Queries as TraceabilityQueries

from events.serial.serial_created import SerialCreated
from events.event_model import EventModel
from events.event_type import EventType
from events.event_manager import EventManager
from events.batch.batch_created import BatchCreatedModel
from events.work_session.work_session_created import WorkSessionCreatedModel
from events.work_order.work_order_started import WorkOrderStartedModel
from utils.production import Queries as ProductionQueries
class JobStartedModel(BaseProductionModel):
  event_type: str = EventType.JOB_STARTED.name

class JobStarted(BaseProduction):
  event_data: JobStartedModel
  stage: str
  def set_model(self, base_model: EventModel):
    self.event_data = JobStartedModel(**base_model.model_dump())


  def apply(self):

    # Check job hasn't been started already
    self._get_job_data()
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
    self.batch = EventManager.trigger_event(self, BatchCreatedModel(
      job_key = self.event_data.job_key,
      work_order_key = self.event_data.work_order_key,
      phase_key = self.event_data.phase_key,
      batch_serials = self.event_data.batch_serials,
      product_key = self.event_data.product_key
    ))['new_batch_out']

    # Create new WorkSession and store _key in Event.info
    self.event_data.work_session_key = EventManager.trigger_event(self, WorkSessionCreatedModel(
      job_key = self.event_data.job_key,
      batch_key = self.batch.key,
      work_order_key = self.event_data.work_order_key,
      phase_key = self.event_data.phase_key,
    ))['work_session_key']

    # Update WorkOrder status
    self.stage = EventManager.trigger_event(self, WorkOrderStartedModel(
      work_order_key = self.event_data.work_order_key
    ))['stage']

    # Update job
    job_update=dict(
      _key = self.event_data.job_key,
      start = self.event_data.timestamp,
      stage = self.stage,
      last_work_session_started = self.event_data.work_session_key,
      active_batch_key = self.batch.key,
      active_batch_qt = self.batch.qt_total,
      active = True,
      assigned_to = self.event_data.user_key,
      last_online = self.event_data.timestamp
    )
    self.job = Job(**self.tx.collection('Job').update(job_update, return_new=True)['new'])

    if add_to_queue:
      update_target_queue(
        job_key = self.event_data.job_key,
        target_key = self.event_data.user_key,
        action = 'add',
        tx = self.tx
      )


    self.set_response(dict(
      message = f"Job {self.event_data.job_key} started",
      batch_data = self.get_batch_execution_data(),
      job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.job.key)).next()
    ))

  def get_batch_execution_data(self):
    batch_execution_data = self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_EXECUTION_DATA,
      # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
      bind_vars=dict(batch_key=self.batch.key if hasattr(self, 'batch') and hasattr(self.batch, 'key') else self.event_data.active_batch_key)
    ).next()
    return batch_execution_data
