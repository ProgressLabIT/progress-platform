from events.production.base_production import BaseProductionEvent, BaseProductionModel
from utils.dt import timestamp
from models.event import EventModel
from models.event import EventType
class JobBackOnlineModel(BaseProductionModel):
  event_type: str = EventType.JOB_BACK_ONLINE.name

class JobBackOnline(BaseProductionEvent):
  event_data: JobBackOnlineModel

  def set_model(self, base_model: EventModel):
    self.info = JobBackOnlineModel(**base_model.model_dump())

  def apply(self):
    updated_work_session = dict(
      _key=self.info.work_session_key,
      active=True,
      end=None
    )
    self.work_session = self.tx.collection('WorkSession').update(
      updated_work_session,
      return_new=True
    )['new']

    # update job as active
    self.set_job_active_state(True)

    self.set_response(self.job)
