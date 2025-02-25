from events.production.base_production import BaseProductionEvent
from events.production.batch_completed import BatchCompletedEvent
from events.serial.serial_updated import SerialUpdatedEvent
from models.event import EventInfoModel, EventType
from models.form import FormFieldValue
from models.serial import SerialFormFieldValue
from models.traceability import *
from utils.production import Queries as ProductionQueries
from utils.serial import Queries as SerialQueries


class StepCompletedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    batch_key: str
    step_key: str
    job_key: str | None = None
    form_data: list[FormFieldValue] | None = None
    batch_serials: list[str] | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.STEP_COMPLETED

  def apply(self):
    batch_record = self.tx.collection('Batch').get(self.info.batch_key)

    if batch_record is None:
      raise ValueError(f"Batch {self.info.batch_key} not found")

    self.batch = Batch(**batch_record)
    self.info.job_key = self.batch.job_key
    self._get_job_data()

    # Save current work session and batch keys in Event.info
    self.work_session = self.get_current_work_session()
    self.info.work_session_key = self.work_session.key

    # Find temporary step data
    try:
      temp_step_data_key = self.tx.collection('StepExecutionData').find(dict(
        batch_key = self.info.active_batch_key,
        step_key = self.info.step_key,
        canceled = None
      )).next()['_key']
    except StopIteration:
      temp_step_data_key = None


    # Create/Update StepExecutionData record
    step_data = StepExecutionData(
      key = temp_step_data_key,
      user_key = self.info.user_key,
      work_session_key = self.info.work_session_key,
      batch_key = self.info.active_batch_key,
      step_key = self.info.step_key,
      job_key = self.info.job_key,
      completed = self.info.timestamp,
      status = StepStatus.DONE,
      form_data = self.info.form_data
    )

    self.tx.collection("StepExecutionData").insert(step_data, overwrite=True)

    if self.info.form_data and self.job.traceability_level:
      batch_serials = [s['_key'] for s in self.tx.aql.execute(
        SerialQueries.GET_BATCH_SERIALS,
        bind_vars=dict(batch_key=self.info.active_batch_key)
      )]

      self.info.batch_serials = batch_serials

      for serial_key in batch_serials:
        serial_data = [SerialFormFieldValue(
          **f.model_dump(),
          serial_key=serial_key
        ) for f in self.info.form_data]

        SerialUpdatedEvent.create_as_child(
          self,
          dict(
            serial_key=serial_key,
            serial_data=serial_data,
          )
        )

    # if last step complete batch
    if self._check_all_batch_steps_done():
      BatchCompletedEvent.create_as_child(
        self,
        dict(
          batch_serials=self.info.batch_serials,
          completed_batch_qt=self.batch.qt_total,
          active_batch_key=self.batch.key,
        ),
      )

    else:
      self.update_job_step_progress()

    # Fetch updated job data and return response
    new_job_data = self.tx.aql.execute(
      ProductionQueries.GET_WORKING_JOB_DATA,
      bind_vars=dict(job_key=self.info.job_key),
    ).next()

    # Set batch to allow fetching updated executiong data in case of new batch
    # (`_get_batch_execution_data()` uses self.batch.key to fetch data)
    self.response = dict(
      message=f"Step completed for batch {self.info.batch_key}",
      job_data=new_job_data,
      batch_data=dict(),
    )

    if new_job_data['active_batch_key'] is not None:
      self.batch = Batch(**self.tx.collection('Batch').get(new_job_data['active_batch_key']))

    self.response['batch_data'] = self.get_batch_execution_data()

