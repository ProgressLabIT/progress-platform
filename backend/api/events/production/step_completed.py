from events.production.base_production import BaseProduction, BaseProductionModel
from models.traceability import *
from utils.production import Queries as ProductionQueries
from models.traceability import *
from models.production import Job
from utils.exceptions import WipNotAvailableError
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from events import EventType, EventManager, BaseEvent, SerialBatchConfirmed, SerialDataUpdated, SerialUpdated, SerialReleased
from events.event_model import EventModel
from events.event_type import EventType
from events.serial.serial_batch_confirmed import SerialBatchConfirmedModel
from events.serial.serial_data_updated import SerialDataUpdatedModel
from events.serial.serial_released import SerialReleasedModel
from events.production.batch_completed import BatchCompletedModel
class StepCompletedModel(BaseProductionModel):
  event_type: str = EventType.STEP_COMPLETED.name

class StepCompleted(BaseProduction):
  event_data: StepCompletedModel

  def set_model(self, base_model: EventModel):
    self.event_data = StepCompletedModel(**base_model.model_dump())

  from events.production.commons.serial import(
    convert_form_data,
    convert_batch_data,
    _convert_field,
    _convert_form_field
  )

  def apply(self):
    self._get_job_data()
    self.get_active_batch()

    # Save current work session and batch keys in Event.info
    if not self.event_data.work_session_key:
      self.work_session = self.get_current_work_session()
      self.event_data.work_session_key = self.work_session.key


    # Create StepExecutionData record
    step_data = StepExecutionData(**vars(self.event_data))
    step_data.batch_key = self.event_data.active_batch_key
    step_data.completed = self.event_data.timestamp
    step_data.status = StepStatus.DONE
    self.tx.collection('StepExecutionData').insert(step_data)

    # if last step complete batch
    if (self.current_step_was_last_to_do()):
      EventManager.notify_event(self, BatchCompletedModel(
        job_key = self.event_data.job_key,
        work_order_key = self.event_data.work_order_key,
        phase_key = self.event_data.phase_key,
        batch_serials = self.event_data.batch_serials,
        completed_batch_qt = self.event_data.completed_batch_qt,
        completed_batch_key = self.event_data.completed_batch_key,
        product_key = self.event_data.product_key,
      ))

    # else update job step progress
    else:
      self.update_job_step_progress()
      new_job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.event_data.job_key)).next()
      if ('wo_bom' in new_job_data):
        setattr(self.job, 'wo_bom', new_job_data['wo_bom'])

      self.set_response(dict(
        message = f"Step completed for batch {self.event_data.active_batch_key}",
        job_data = self.job,
        batch_data = self.get_batch_execution_data()
      ))


  def store_batch_data(self, batch_execution_data):
    if (len(batch_execution_data) > 0):
      EventManager.notify_event(self, SerialDataUpdatedModel(
        batch_key = self.event_data.active_batch_key,
        batch_execution_data = batch_execution_data,
        user_key = self.event_data.user_key
      ))
